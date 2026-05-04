
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import IDeleteMovie


class DeleteMovie(IDeleteMovie):
    def __init__(
        self,
        movie_repository: IMoviesRepository
    ):
        self.movie_repository = movie_repository
    
    async def delete_movie_by_id(self,id):
        result = await self.movie_repository.delete_movie_by_id(id)

        if not result: #ko thanh cong
            return None
        return "Xóa thành công"