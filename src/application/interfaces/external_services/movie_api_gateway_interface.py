
from typing import Protocol


class IMovieApiGateway(Protocol):
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
