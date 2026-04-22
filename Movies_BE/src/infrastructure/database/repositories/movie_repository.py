
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository


class MoviesRepositories(IMoviesRepository):
    
    async def fetch_movies_list(self):
        print(" Vào được repo này")
        return {"message": "Test thanh cong"}