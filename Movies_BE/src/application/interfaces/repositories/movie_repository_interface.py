
from typing import Protocol


class IMoviesRepository(Protocol):
    async def fetch_movies_list(self):
        ...

    async def fetch_movie_detail_by_name(
            self,
            name: str
        ):
        ...

