# Chỗ này là config về tiêm phụ thuộc

from fastapi import Depends

from src.infrastructure.services.movie_collection.add_movie_to_collection import AddMovieToCollection
from src.infrastructure.services.movie_collection.create_movie_collection import CreateMovieCollection
from src.infrastructure.services.movie_collection.create_movie_collection import CreateMovieCollection
from src.infrastructure.services.movie_collection.get_favourite_list import GetCollectionService
from src.application.interfaces.services.collection_service_interface import IAddMovieToCollectionService, ICreateCollectionService, IGetCollectionService
from src.infrastructure.database.repositories.movie_collection_repository import CollectionRepository
from src.infrastructure.services.users.login_user_service import LoginUser
from src.application.interfaces.services.users_service_interface import ICreateUserService, ILoginUser
from src.infrastructure.services.users.create_users_service import CreateUserService
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.infrastructure.services.movie.delete_movie import DeleteMovie
from src.infrastructure.services.movie.patch_movie import PatchMovie
from src.infrastructure.services.movie.update_movie import UpdateEntireMovie
from src.infrastructure.services.movie.create_movie import CreateMovie
from src.application.interfaces.external_services.movie_api_gateway_interface import IMovieApiGateway
from src.infrastructure.external_services.movie_api_gateway import MovieApiGateway
from src.infrastructure.services.movie.get_movie_by_id import GetMoviesDetailById
from src.infrastructure.services.movie.get_movie_by_name import GetMoviesDetailByName
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import ICreateMovie, IDeleteMovie, IGetListMoviesService, IGetMoviesDetailById, IGetMoviesDetailByName, IPatchMovie, IUpdateEntireMovie
from src.infrastructure.database.repositories.movie_repository import MoviesRepositories
from src.infrastructure.services.movie.get_movie_list import GetListMovies
from sqlalchemy.orm import Session
from src.infrastructure.database.session import get_db

def IMoviesExternalServiceDependency():
    return MovieApiGateway()

def IMoviesRepositoryDependency(db: Session = Depends(get_db)):
    # Nhận db từ Depends(get_db) và nhét vào Repository
    return MoviesRepositories(db=db)

def IUserRepositoryDependency(db: Session = Depends(get_db)):
    return UserRepository(db=db)

def ICollectionRepositoryDependency(db: Session = Depends(get_db)):
    return CollectionRepository(db=db)


# Bơm phụ thuộc
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

def IDeleteMovieDependency(
    movie_repository: IMoviesRepository = Depends(IMoviesRepositoryDependency)
)-> IDeleteMovie:
    return DeleteMovie(
        movie_repository=movie_repository
    )


#========== User Service Dependencies ==========

def ICreateUserDependency(
    user_repository: IUserRepositoryDependency = Depends(IUserRepositoryDependency)
) -> ICreateUserService:
    return CreateUserService(
        user_repository=user_repository
    )

def ILoginUserDependency(
    user_repository: IUserRepositoryDependency = Depends(IUserRepositoryDependency)
) -> ILoginUser:
    return LoginUser(
        user_repository= user_repository
    )

#========== Collection Service Dependencies ==========

def IGetCollectionServiceDependency(
    collection_repository: ICollectionRepositoryDependency = Depends(ICollectionRepositoryDependency)
) -> IGetCollectionService:
    return GetCollectionService(
        collection_repository=collection_repository
    )

def ICreateCollectionServiceDependency(
    collection_repository: ICollectionRepositoryDependency = Depends(ICollectionRepositoryDependency)
) -> ICreateCollectionService:
    return CreateMovieCollection(
        collection_repository=collection_repository
    )

def IAddMovieToCollectionServiceDependency(
    collection_repository: ICollectionRepositoryDependency = Depends(ICollectionRepositoryDependency)
) -> IAddMovieToCollectionService:
    return AddMovieToCollection(
        collection_repository=collection_repository
    )