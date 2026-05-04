
from typing import Any

from src.application.interfaces.services.movies_service_interface import IGetMoviesDetailById
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository


class GetMoviesDetailById(IGetMoviesDetailById):
    def __init__(
        self, 
        movie_repository: IMoviesRepository
    ):
        self.movie_repository = movie_repository

    async def fetch_movie_detail_by_id(self, id: str) -> Any:
        print("Vào được fetch_movie_detail_by_id")
        result = await self.movie_repository.fetch_movie_detail_by_id(id)

        if not result: #ko thanh cong
            return None
        return result