import json
import logging

from fastapi.encoders import jsonable_encoder

from src.infrastructure.cache.movie_cache import cache_get_json, cache_set_json
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import IHabitSimilarMoviesService
from src.application.interfaces.services.similar_movies_interface import ISimilarMoviesService

logger = logging.getLogger(__name__)


class HabitSimilarMoviesService(IHabitSimilarMoviesService):

    def __init__(self, redis, similar_movies_service: ISimilarMoviesService, movie_repository:IMoviesRepository):
        self.redis = redis
        self.similar_movies_service = similar_movies_service
        self.movie_repository = movie_repository 

    async def get_habit_similar_movies(self, movie_id: str, limit: int = 5) -> list[dict]:
        cache_key = f"movie:{movie_id}:habit"

        try:    
            cached = await cache_get_json(self.redis, cache_key)
        except Exception as e:
            logger.warning(f"Redis lỗi khi đọc '{cache_key}': {e}")
            cached = None

        if cached:
            similar_ids = cached[:limit]
            movies = await self.movie_repository.get_movies_by_ids(similar_ids)
            movies_by_id = {m["id"]: m for m in movies}
            ordered = [movies_by_id[i] for i in similar_ids if i in movies_by_id]
            if ordered:
                return ordered

        es_result = await self.similar_movies_service.get_similar_movies(movie_id, limit)

        if es_result:

            return es_result

        # Fallback 2 — cùng category (DB)
        return await self.movie_repository.get_movies_by_category_of(movie_id, limit)