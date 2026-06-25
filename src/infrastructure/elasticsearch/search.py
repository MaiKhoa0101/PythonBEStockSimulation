from src.infrastructure.elasticsearch.es_client import es_client, MOVIE_INDEX


def _parse_hit(hit: dict) -> dict:
    source = hit.get("_source", {})
    return {
        "id":           source.get("id"),
        "name":         source.get("name"),
        "origin_name":  source.get("origin_name"),
        "slug_name":    source.get("slug_name"),
        "description":  source.get("description"),
        "poster_url":   source.get("poster_url"),
        "thumb_url":    source.get("thumb_url"),
        "year":         source.get("year"),
        "view":         source.get("view"),
        "status":       source.get("status"),
        "quality":      source.get("quality"),
        "lang":         source.get("lang"),
        "is_series":    source.get("is_series"),
        "chieurap":     source.get("chieurap"),
        "is_deleted":   source.get("is_deleted"),
        "actors":       source.get("actors", []),
        "directors":    source.get("directors", []),
        "categories":   source.get("categories", []),
        "countries":    source.get("countries", []),
        "episodes":     source.get("episodes", []),
        "_score":       hit.get("_score"),
    }


def search_movies(query: str, size: int = 20) -> dict:
    response = es_client.search(
        index=MOVIE_INDEX,
        size=size,
        query={
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
    )
    return {
        "total": response["hits"]["total"]["value"],
        "results": [_parse_hit(hit) for hit in response["hits"]["hits"]]
    }