
from typing import Protocol

from fastapi import UploadFile

from src.domain.entities.movies.movie import Movie


class IMoviesRepository(Protocol):
    async def fetch_movies_list(self):
        ...

    async def fetch_movie_detail_by_name(
        self,
        name: str
    ):
        ...
    async def fetch_movie_detail_by_name_no_auth(
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
        
    async def upload_episode(
        local_path: str,
        episode_id: str
    ):
        ...

    async def get_url_episode(
        id_episode:str
    ):
        ...