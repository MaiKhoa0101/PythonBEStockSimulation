from dataclasses import fields
from typing import List, Optional

from src.domain.entities.movies.movie import Movie
from src.infrastructure.elasticsearch.es_client import es_client, MOVIE_INDEX
from src.infrastructure.elasticsearch.search import _parse_hit


def fetch_movies_list_from_es(
    page: int = 1,
    size: int = 20,
    filters: Optional[dict] = None
) -> dict:
    must_filters = [{"term": {"is_deleted": False}}]

    if filters:
        filter_fields = ["year", "status", "quality", "lang", "is_series", "chieurap"]
        for field in filter_fields:
            value = filters.get(field)
            if value is not None:
                must_filters.append({"term": {field: value}})

    response = es_client.search(
        index=MOVIE_INDEX,
        from_=(page - 1) * size, 
        size=size,
        query={"bool": {"filter": must_filters}},
        sort=[{"view": {"order": "desc"}}]
    )
    return {
        "total": response["hits"]["total"]["value"],
        "page": page,
        "size": size,
        "results": [_parse_hit(hit) for hit in response["hits"]["hits"]]
    }

def fetch_movies_list_home_from_es(
    page: int = 1,
    size: int = 20,
    filters: Optional[dict] = None
) -> List[Movie]:
    must_filters = [{"term": {"is_deleted": False}}]

    if filters:
        filter_fields = ["year", "status", "quality", "lang", "is_series", "chieurap"]
        for field in filter_fields:
            value = filters.get(field)
            if value is not None:
                must_filters.append({"term": {field: value}})

    response = es_client.search(
        index=MOVIE_INDEX,
        from_=(page - 1) * size, 
        size=size,
        query={"bool": {"filter": must_filters}},
        sort=[{"view": {"order": "desc"}}]
    )
    
    movie_dataclass_fields = {f.name for f in fields(Movie)}
    movie_entities: List[Movie] = []
    
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        
        if "id" not in source or not source["id"]:
            source["id"] = hit.get("_id")
            
        clean_data = {k: v for k, v in source.items() if k in movie_dataclass_fields}
        
        movie_entities.append(Movie(**clean_data))
        
    return movie_entities

def get_movie_by_slug_from_es(slug_name: str) -> Optional[dict]:
    response = es_client.search(
        index=MOVIE_INDEX,
        size=1,
        query={
            "bool": {
                "filter": [
                    {"term": {"slug_name": slug_name}},
                    {"term": {"is_deleted": False}},
                ]
            }
        }
    )
    hits = response["hits"]["hits"]
    if not hits:
        return None 

    return _parse_hit(hits[0])