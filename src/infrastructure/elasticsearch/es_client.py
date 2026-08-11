import os
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, ConnectionError as ESConnectionError, TransportError

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")

es_client = Elasticsearch(ES_URL)

MOVIE_INDEX = "movies"

_NESTED_ENTITY_PROPERTIES = {
    "type": "nested",
    "properties": {
        "id":   {"type": "keyword"},
        "name": {
            "type": "text",
            "analyzer": "vi_analyzer",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "slug": {"type": "keyword"},
    },
}

MOVIE_INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "vi_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id":           {"type": "keyword"},
            "name":         {"type": "text", "analyzer": "vi_analyzer", "fields": {"keyword": {"type": "keyword"}}},
            "origin_name":  {"type": "text", "analyzer": "vi_analyzer"},
            "description":  {"type": "text", "analyzer": "vi_analyzer"},

            # FIX: trước đây là text/keyword phẳng (chỉ chứa tên) — giờ là
            # nested object đầy đủ id/name/slug, đồng nhất với API list-movie.
            "actors":       _NESTED_ENTITY_PROPERTIES,
            "directors":    _NESTED_ENTITY_PROPERTIES,
            "categories":   _NESTED_ENTITY_PROPERTIES,
            "countries":    _NESTED_ENTITY_PROPERTIES,

            "slug_name":    {"type": "keyword"},
            "poster_url":   {"type": "keyword"},
            "thumb_url":    {"type": "keyword"},
            "year":         {"type": "integer"},
            "view":         {"type": "integer"},
            "is_deleted":   {"type": "boolean"},
            "status":       {"type": "keyword"},
            "quality":      {"type": "keyword"},
            "lang":         {"type": "keyword"},
            "is_series":    {"type": "boolean"},
            "chieurap":     {"type": "boolean"},
            # Field này cần có để reconcile_task.py so sánh độ mới ES vs DB.
            "updated_at":   {"type": "date"},

            "episodes": {
                "type": "nested",
                "properties": {
                    "id":           {"type": "keyword"},
                    "name_episode": {"type": "text", "analyzer": "vi_analyzer"},
                    "slug":         {"type": "keyword"},
                    "filename":     {"type": "keyword"},
                    "link_embed":   {"type": "keyword"},
                    "link_m3u8":    {"type": "keyword"},
                    "server_name":  {"type": "keyword"},
                    "description":  {"type": "text", "analyzer": "vi_analyzer"}
                }
            }
        }
    }
}


def create_movie_index():
    """Chỉ tạo index nếu CHƯA tồn tại — dùng lúc bootstrap lần đầu.
    Không dùng hàm này để sửa mapping của index đã tồn tại (ES không cho
    đổi mapping field đã có kiểu dữ liệu khác) — dùng recreate_movie_index()."""
    if not es_client.indices.exists(index=MOVIE_INDEX):
        es_client.indices.create(index=MOVIE_INDEX, body=MOVIE_INDEX_MAPPING)
        print(f"[Elasticsearch] Đã tạo index '{MOVIE_INDEX}'")
    else:
        print(f"[Elasticsearch] Index '{MOVIE_INDEX}' đã tồn tại")


def recreate_movie_index():
    print(f"[Elasticsearch] Xóa index '{MOVIE_INDEX}' cũ và tạo lại với mapping mới")
    if es_client.indices.exists(index=MOVIE_INDEX):
        es_client.indices.delete(index=MOVIE_INDEX)
        print(f"[Elasticsearch] Đã xóa index cũ '{MOVIE_INDEX}'")
    es_client.indices.create(index=MOVIE_INDEX, body=MOVIE_INDEX_MAPPING)
    print(f"[Elasticsearch] Đã tạo lại index '{MOVIE_INDEX}' với mapping mới")


def get_similar_movies_from_es(movie_id: str, limit: int = 10) -> list[dict]:
    """
    Raise NotFoundError nếu movie_id không tồn tại trong index.
    Raise ESConnectionError/TransportError nếu ES mất kết nối.
    Caller (service layer) chịu trách nhiệm bắt các exception này.
    """
    query = {
        "size": limit,
        "_source": ["id", "name", "slug_name", "poster_url", "is_series", "year"],
        "query": {
            "bool": {
                "must": {
                    "more_like_this": {
                        "fields": ["name","origin_name", "description", "categories.name"],
                        "like": [{"_index": MOVIE_INDEX, "_id": movie_id}],
                        "min_term_freq": 1,
                        "max_query_terms": 12,
                        "minimum_should_match": "30%",
                    }
                },
                "filter": [
                    {"term": {"is_deleted": False}}
                ],
            }
        },
    }

    response = es_client.search(index=MOVIE_INDEX, body=query)
    hits = response.get("hits", {}).get("hits", [])
    return [hit["_source"] for hit in hits]