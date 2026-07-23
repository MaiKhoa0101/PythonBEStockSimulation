import os
from elasticsearch import Elasticsearch

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")

es_client = Elasticsearch(ES_URL)

MOVIE_INDEX = "movies"

# Object dùng chung cho actors/directors/categories/countries — mỗi phần tử
# giờ là {id, name, slug} đầy đủ thay vì chỉ 1 string tên, khớp với
# ActorDTO/DirectorDTO/CategoryDTO/CountryDTO mà API list (đọc từ Postgres)
# đang trả về. "name" vẫn giữ vi_analyzer để full-text search tiếng Việt +
# subfield "keyword" để filter/sort chính xác theo tên, "id"/"slug" là
# keyword để filter chính xác theo id/slug.
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
    """Xóa index cũ (mapping sai/lỗi thời) và tạo lại với MOVIE_INDEX_MAPPING
    hiện tại. Dùng khi đổi schema document (như lần sửa categories/countries
    từ string sang object) — bắt buộc phải xóa vì ES không cho đổi kiểu field
    đã map sẵn. Gọi xong nhớ chạy lại bulk sync để nạp lại toàn bộ dữ liệu."""
    if es_client.indices.exists(index=MOVIE_INDEX):
        es_client.indices.delete(index=MOVIE_INDEX)
        print(f"[Elasticsearch] Đã xóa index cũ '{MOVIE_INDEX}'")
    es_client.indices.create(index=MOVIE_INDEX, body=MOVIE_INDEX_MAPPING)
    print(f"[Elasticsearch] Đã tạo lại index '{MOVIE_INDEX}' với mapping mới")


if __name__ == "__main__":
    recreate_movie_index()