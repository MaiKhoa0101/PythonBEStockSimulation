from slugify import slugify

from src.infrastructure.database.repositories import stock_repository
from src.application.interfaces.services.movies_data_interface import IMoviesService
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository

class GetListMovies(IMoviesService):

    def __init__(self, movie_repository: IMoviesRepository):
        self.movie_repository = movie_repository

    async def fetch_movies_list(self):
        print(" Vào được đây")

        data = await self.movie_repository.fetch_movies_list()
        if (not data):
            pass
            # Chỗ này nên tìm cách cho retry bao nhiêu lần đó 
            # trước khi nhả ra lỗi.
            # Hmm, mà nhả ra lỗi thì trả về cái gì? None à :v
        return data
    
    async def fetch_movie_detail_by_name(self, name: str):
        #Xử lí name thành định dạng không dấu và gạch ngang như one piece -> one-piece
        formatted_name = slugify(name)
        return await self.movie_repository.fetch_movie_detail_by_name(formatted_name)