
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import IGetVideoUrlService


class GetVideoUrlService(IGetVideoUrlService):
    def __init__(
            self, 
            movie_repository: IMoviesRepository, 
        ):
        self.movie_repository = movie_repository

    async def get_video_url(self, id_episode:str):
        print(" Vào được đây")
        data = await self.movie_repository.get_url_episode(id_episode)
        return data