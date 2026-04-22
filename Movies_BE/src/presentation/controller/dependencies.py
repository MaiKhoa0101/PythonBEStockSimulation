# Chỗ này là config về tiêm phụ thuộc

from fastapi import Depends

from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_data_interface import IMoviesService
from src.infrastructure.database.repositories.movie_repository import MoviesRepositories
from src.infrastructure.services.get_movie_list import GetListMovies

def get_movies_repository() -> IMoviesRepository:
    return MoviesRepositories()

# Bơm 
def IMoviesServiceDependency() -> IMoviesService:
    return GetListMovies(
        movie_repository=get_movies_repository()
    )

def IMoviesRepositoryDependency() -> IMoviesRepository:
    return MoviesRepositories()
