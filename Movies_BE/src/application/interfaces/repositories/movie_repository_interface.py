
from typing import Protocol

from src.domain.entities.movie import Movie


class IMoviesRepository(Protocol):
    async def fetch_movies_list(self):
        ...

    async def fetch_movie_detail_by_name(
        self,
        name: str
    ):
        ...
    async def fetch_movie_detail_by_id(
        self,
        id: str
    ):
        ...

    async def create_movie(
        self,
        movie_entity: Movie
    ):
        ...

    async def update_entire_movie(
        self,
        movie_entity: Movie
    ):
        ...

    async def patch_movie(
        self,
        movie_entity: Movie
    ): 
        ...

    async def upsert_episode(
        self,
        movie_entity: Movie
    ):
        ...

    async def delete_movie_by_id(
        self,
        id: str
    ):
        ...

    