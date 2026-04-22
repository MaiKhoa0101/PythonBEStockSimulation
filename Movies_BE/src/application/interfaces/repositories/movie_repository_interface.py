
from typing import Protocol


class IMoviesRepository(Protocol):
    async def fetch_movies_list(self):
        ...
