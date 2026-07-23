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
                        "bool": {
                            "should": [
                                # Các field text phẳng — multi_match bình thường vẫn dùng được
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["name^3", "origin_name^2", "description"],
                                        "fuzziness": "AUTO"
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "actors",
                                        "query": {
                                            "match": {
                                                "actors.name": {
                                                    "query": query,
                                                    "fuzziness": "AUTO"
                                                }
                                            }
                                        },
                                        "score_mode": "max"
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "directors",
                                        "query": {
                                            "match": {
                                                "directors.name": {
                                                    "query": query,
                                                    "fuzziness": "AUTO"
                                                }
                                            }
                                        },
                                        "score_mode": "max"
                                    }
                                },
                                {
                                    "nested": {
                                        "path": "countries",
                                        "query": {
                                            "match": {
                                                "countries.name": {
                                                    "query": query,
                                                    "fuzziness": "AUTO"
                                                }
                                            }
                                        },
                                        "score_mode": "max"
                                    }
                                }
                            ],
                            "minimum_should_match": 1
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


def _build_category_filter(category_slug: str) -> dict:
    """Ví dụ filter theo thể loại — cũng phải bọc nested vì categories.slug
    nằm trong path nested "categories"."""
    return {
        "nested": {
            "path": "categories",
            "query": {"term": {"categories.slug": category_slug}}
        }
    }


def _build_country_filter(country_slug: str) -> dict:
    return {
        "nested": {
            "path": "countries",
            "query": {"term": {"countries.slug": country_slug}}
        }
    }