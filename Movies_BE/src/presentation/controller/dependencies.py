# Chỗ này là config về tiêm phụ thuộc

from fastapi import Depends

from src.infrastructure.services.movie.patch_movie import PatchMovie
from src.infrastructure.services.movie.update_movie import UpdateEntireMovie
from src.infrastructure.services.movie.create_movie import CreateMovie
from src.application.interfaces.external_services.movie_api_gateway_interface import IMovieApiGateway
from src.infrastructure.external_services.movie_api_gateway import MovieApiGateway
from src.infrastructure.services.movie.get_movie_by_id import GetMoviesDetailById
from src.infrastructure.services.movie.get_movie_by_name import GetMoviesDetailByName
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import ICreateMovie, IGetListMoviesService, IGetMoviesDetailById, IGetMoviesDetailByName, IPatchMovie, IUpdateEntireMovie
from src.infrastructure.database.repositories.movie_repository import MoviesRepositories
from src.infrastructure.services.movie.get_movie_list import GetListMovies
from sqlalchemy.orm import Session
from src.infrastructure.database.session import get_db

def IMoviesExternalServiceDependency():
    return MovieApiGateway()

def IMoviesRepositoryDependency(db: Session = Depends(get_db)):
    # Nhận db từ Depends(get_db) và nhét vào Repository
    return MoviesRepositories(db=db)
# Bơm 
def IGetListMoviesServiceDependency(
    movie_repository: IMoviesRepository = Depends(IMoviesRepositoryDependency),
    movie_external_service: IMovieApiGateway = Depends(IMoviesExternalServiceDependency) 
) -> IGetListMoviesService:
    return GetListMovies(
        movie_repository=movie_repository,
        movie_external_service= movie_external_service
        )

def IGetMoviesDetailByNameDependency(
    movie_repository: IMoviesRepository = Depends(IMoviesRepositoryDependency)
) -> IGetMoviesDetailByName:
    return GetMoviesDetailByName(movie_repository=movie_repository)

def IGetMoviesDetailByIdDependency(
    movie_repository: IMoviesRepository = Depends(IMoviesRepositoryDependency)
) -> IGetMoviesDetailById:
    return GetMoviesDetailById(movie_repository=movie_repository)


def ICreateMovieDependency(
    movie_repository: IMoviesRepository = Depends(IMoviesRepositoryDependency)
) -> ICreateMovie:
    return CreateMovie(
        movie_repository = movie_repository
    )

def IUpdateEntireMovieDependency(
    movie_repository: IMoviesRepository = Depends(IMoviesRepositoryDependency)
) -> IUpdateEntireMovie:
    return UpdateEntireMovie(
        movie_repository= movie_repository
    )

def IPatchMovieDependency(
    movie_repository: IMoviesRepository = Depends(IMoviesRepositoryDependency)
) -> IPatchMovie:
    return PatchMovie(
        movie_repository= movie_repository
    )