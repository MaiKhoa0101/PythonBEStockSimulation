from abc import ABC, abstractmethod
from typing import List, Dict, Protocol


class ISimilarMoviesService(Protocol):
    async def get_similar_movies(self, movie_id: str, limit: int = 5) -> list[dict]:
        ...