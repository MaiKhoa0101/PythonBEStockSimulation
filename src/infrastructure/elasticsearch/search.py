from src.infrastructure.elasticsearch.es_client import es_client, MOVIE_INDEX

from elasticsearch import AsyncElasticsearch

def search_movies(query: str, size: int = 20):
    """
    Tìm kiếm nâng cao và trả về ĐẦY ĐỦ thông tin chi tiết của bộ phim,
    bao gồm tất cả các trường thuộc tính và danh sách tập phim liên quan từ ES.
    """
    body = {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "name^3",
                                "origin_name^2",
                                "description",
                                "actors",
                                "directors"
                            ],
                            "fuzziness": "AUTO"
                        }
                    }
                ],
                "filter": [
                    {"term": {"is_deleted": False}}
                ]
            }
        }
    }

    response = es_client.search(index=MOVIE_INDEX, body=body)

    results = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        
        results.append({
            "id": source.get("id"),
            "name": source.get("name"),
            "slug_name": source.get("slug_name"),
            "origin_name": source.get("origin_name"),
            "is_series": source.get("is_series", False),
            "status": source.get("status"),
            "description": source.get("description"),
            
            "poster_url": source.get("poster_url"),
            "thumb_url": source.get("thumb_url"),
            "trailer_url": source.get("trailer_url"),
            
            "quality": source.get("quality"),
            "lang": source.get("lang"),
            "time": source.get("time"),
            "year": source.get("year"),
            "view": source.get("view", 0),
            
            "episode_current": source.get("episode_current"),
            "episode_total": source.get("episode_total"),
            
            "is_copyright": source.get("is_copyright", False),
            "sub_docquyen": source.get("sub_docquyen", False),
            "chieurap": source.get("chieurap", False),
            "notify": source.get("notify"),
            "showtimes": source.get("showtimes"),
            
            "actors": source.get("actors"),
            "directors": source.get("directors"),
            "categories": source.get("categories"),
            "countries": source.get("countries"),

            "episodes": source.get("episodes", []),
            
            "is_deleted": source.get("is_deleted", False),
            "created_at": source.get("created_at"),
            "created_by": source.get("created_by"),
            "updated_at": source.get("updated_at"),
            "updated_by": source.get("updated_by"),
            "score": hit.get("_score")
        })

    return {
        "total": response["hits"]["total"]["value"],
        "results": results
    }