# Phương án 2
from slugify import slugify

from src.application.interfaces.services.movies_service_interface import IGetListMoviesService, IGetMoviesDetailByName
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository

    
class GetMoviesDetailByName(IGetMoviesDetailByName):
    def __init__(self, movie_repository: IMoviesRepository):
        self.movie_repository = movie_repository

    async def fetch_movie_detail_by_name(self, name: str):
        #Xử lí name thành định dạng không dấu và gạch ngang như one piece -> one-piece
        formatted_name = slugify(name)
        result = await self.movie_repository.fetch_movie_detail_by_name(formatted_name)
        if not result: #ko thanh cong
            return None
        return result