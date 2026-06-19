import os
from elasticsearch import Elasticsearch

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")

es_client = Elasticsearch(ES_URL)

MOVIE_INDEX = "movies"

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
            "actors":       {"type": "text", "analyzer": "vi_analyzer"},
            "directors":    {"type": "text", "analyzer": "vi_analyzer"},
            "categories":   {"type": "text", "analyzer": "vi_analyzer"},  
            "countries":    {"type": "keyword"}, 
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
        }
    }
}


def create_movie_index():
    if not es_client.indices.exists(index=MOVIE_INDEX):
        es_client.indices.create(index=MOVIE_INDEX, body=MOVIE_INDEX_MAPPING)
        print(f"[Elasticsearch] Đã tạo index '{MOVIE_INDEX}'")
    else:
        print(f"[Elasticsearch] Index '{MOVIE_INDEX}' đã tồn tại")