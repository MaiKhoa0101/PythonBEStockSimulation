import json
import logging
from elasticsearch.exceptions import NotFoundError, ConnectionError as ESConnectionError, TransportError

from elasticsearch import NotFoundError

from src.infrastructure.cache.movie_cache import cache_get_json, cache_set_json
from src.infrastructure.elasticsearch.es_client import get_similar_movies_from_es
from src.application.interfaces.services.similar_movies_interface import ISimilarMoviesService

logger = logging.getLogger(__name__)
CACHE_TTL = 3600
class SimilarMoviesService(ISimilarMoviesService): 
    def __init__(self, redis):
        self.redis = redis

    async def get_similar_movies(self, movie_id: str, limit: int = 5):
        cache_key = f"movie:{movie_id}:similar"

        try:
            cached = await cache_get_json(self.redis, cache_key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(f"Redis lỗi khi đọc cache '{cache_key}': {e}")

        try:
            movies = get_similar_movies_from_es(movie_id, limit)
        except NotFoundError:
            logger.info(f"movie_id '{movie_id}' không tồn tại trong ES index, bỏ qua gợi ý")
            return []
        except (ESConnectionError, TransportError) as e:
            logger.error(f"Elasticsearch mất kết nối khi lấy similar movies cho '{movie_id}': {e}")
            return []
        except Exception as e:
            logger.error(f"Lỗi không xác định khi lấy similar movies cho '{movie_id}': {e}", exc_info=True)
            return []

        try:
            await cache_set_json(self.redis, cache_key, movies, expire=CACHE_TTL)
        except Exception as e:
            logger.warning(f"Redis lỗi khi ghi cache '{cache_key}': {e}")

        return movies