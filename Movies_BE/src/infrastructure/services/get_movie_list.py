from slugify import slugify

from src.application.interfaces.external_services.movie_api_gateway_interface import IMovieApiGateway
from src.application.interfaces.services.movies_service_interface import IGetListMoviesService
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository


class GetListMovies(IGetListMoviesService):
    def __init__(
            self, 
            movie_repository: IMoviesRepository, 
            movie_external_service: IMovieApiGateway
        ):
        self.movie_repository = movie_repository
        self.movie_external_service = movie_external_service

    async def fetch_movies_list(self):
        print(" Vào được đây")
        data = await self.movie_repository.fetch_movies_list()
        if (not data):
            data = await self.movie_external_service.fetch_movies_list()
        return data