# Chỗ này là config về tiêm phụ thuộc

from fastapi import Depends

from src.infrastructure.services.get_movie_by_name import GetMoviesDetailByName
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_data_interface import IGetListMoviesService, IGetMoviesDetailByName
from src.infrastructure.database.repositories.movie_repository import MoviesRepositories
from src.infrastructure.services.get_movie_list import GetListMovies


def IMoviesRepositoryDependency() -> IMoviesRepository:
    return MoviesRepositories()
# Bơm 
def IGetListMoviesServiceDependency() -> IGetListMoviesService:
    return GetListMovies(
        movie_repository=IMoviesRepositoryDependency()
    )

def IGetMoviesDetailByNameDependency() -> IGetMoviesDetailByName:
    return GetMoviesDetailByName(
        movie_repository=IMoviesRepositoryDependency()
    )

