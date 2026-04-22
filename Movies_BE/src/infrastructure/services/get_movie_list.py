from slugify import slugify

from src.application.interfaces.services.movies_data_interface import IGetListMoviesService
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository


class GetListMovies(IGetListMoviesService):
    def __init__(self, movie_repository: IMoviesRepository):
        self.movie_repository = movie_repository

    async def fetch_movies_list(self):
        print(" Vào được đây")

        data = await self.movie_repository.fetch_movies_list()
        if (not data):
            pass
            # Chỗ này nên tìm cách cho retry bao nhiêu lần đó 
            # trước khi nhả ra lỗi.
        return data