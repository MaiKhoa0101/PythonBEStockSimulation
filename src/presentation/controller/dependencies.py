# Chỗ này là config về tiêm phụ thuộc

from fastapi import Depends

from src.application.interfaces.repositories.admin_log_repository_interface import IAdminLogRepository
from src.application.interfaces.services.admin_log_service_interface import IAdminLogService
from src.infrastructure.database.repositories.admin_log_repository import AdminLogRepository
from src.infrastructure.services.logs.admin_log_service import AdminLogService
from src.application.interfaces.services.log_service_interface import ILogService
from src.infrastructure.services.logs.log_service import LogService
from src.infrastructure.database.repositories.log_repository import LogRepository
from src.infrastructure.services.movie.get_video_url import GetVideoUrlService
from src.application.interfaces.services.short_service_interface import IShortService
from src.infrastructure.services.short.short_service import ShortService
from src.application.interfaces.repositories.short_repository_interface import IShortRepository
from src.infrastructure.database.repositories.short_repository import ShortRepository
from src.infrastructure.services.users.get_user_by_id import GetUserById
from src.infrastructure.services.users.update_user_by_id import UpdateUser
from src.application.interfaces.services.transaction_service import ITransactionService
from src.infrastructure.database.repositories.transaction_repository import TransactionRepository
from src.infrastructure.services.transaction.transaction_service import TransactionService
from src.infrastructure.services.subscription.subscription_service import SubscriptionService
from src.application.interfaces.services.subscription_service import ISubscriptionService
from src.infrastructure.database.repositories.subscription_repository import SubscriptionRepository
from src.infrastructure.services.movie.upload_episode import UploadEpisode
from src.infrastructure.services.movie_collection.add_movie_to_collection import AddMovieToCollection
from src.infrastructure.services.movie_collection.create_movie_collection import CreateMovieCollection
from src.infrastructure.services.movie_collection.create_movie_collection import CreateMovieCollection
from src.infrastructure.services.movie_collection.get_favourite_list import GetCollectionService
from src.application.interfaces.services.collection_service_interface import IAddMovieToCollectionService, ICreateCollectionService, IGetCollectionService
from src.infrastructure.database.repositories.movie_collection_repository import CollectionRepository
from src.infrastructure.services.users.login_user_service import LoginUser
from src.application.interfaces.services.users_service_interface import ICreateUserService, IGetUserById, ILoginUser, IUpdateUser
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
from src.application.interfaces.services.movies_service_interface import ICreateMovie, IDeleteMovie, IGetListMoviesService, IGetMoviesDetailById, IGetMoviesDetailByName, IGetVideoUrlService, IPatchMovie, IUpdateEntireMovie, IUploadEpisode
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

def ISubscriptionRepositoryDependency(db:Session = Depends(get_db)):
    return SubscriptionRepository(db=db)

def ITransactionRepositoryDependency(db:Session = Depends(get_db)):
    return TransactionRepository(db=db)

def IShortRepositoryDependency(db:Session = Depends(get_db)):
    return ShortRepository(db=db)

def ILogRepositoryDependency(db:Session = Depends(get_db)):
    return LogRepository(db=db)

def IAdminLogRepositoryDependency(db: Session = Depends(get_db)) -> IAdminLogRepository:
    return AdminLogRepository(db=db)
 
#=================================================ok
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

def IUploadEpisodeServiceDepedency(
    movie_repository: IMoviesRepository = Depends(IMoviesRepositoryDependency)
)-> IUploadEpisode:
    return UploadEpisode(
        movie_repository=movie_repository
    )

def IGetVideoUrlServiceDependency(
    movie_repository: IMoviesRepository = Depends(IMoviesRepositoryDependency)
)-> IGetVideoUrlService:
    return GetVideoUrlService(
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

def IUserUpdateDependency(
    user_repository: IUserRepositoryDependency = Depends(IUserRepositoryDependency)
) -> IUpdateUser:
    return UpdateUser(
        user_repository= user_repository
    )

def IUserGetByIdDependency(
    user_repository: IUserRepositoryDependency = Depends(IUserRepositoryDependency)
) -> IGetUserById:
    return GetUserById(
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


def ISubscriptionServiceDependency(
    subscription_repository: ISubscriptionRepositoryDependency= Depends(ISubscriptionRepositoryDependency),
)-> ISubscriptionService:
    return SubscriptionService(
        subscription_repo=subscription_repository,
    )


def ITransactionServiceDependency(
    transaction_repository: ITransactionRepositoryDependency= Depends(ITransactionRepositoryDependency),
    subscription_repository: ISubscriptionRepositoryDependency= Depends(ISubscriptionRepositoryDependency),
    user_update: IUserUpdateDependency = Depends(IUserUpdateDependency),
    user_get_by_id: IUserGetByIdDependency = Depends(IUserGetByIdDependency)

)-> ITransactionService:
    return TransactionService(
        transaction_repository=transaction_repository,
        subscription_repository=subscription_repository,
        user_update = user_update,
        user_get_by_id=user_get_by_id
    )

def IShortServiceDependency(
    short_repository:IShortRepositoryDependency = Depends(IShortRepositoryDependency)
)-> IShortService:
    return ShortService(
        short_repository = short_repository
    )

def ILogServiceDependency(
    log_repository:ILogRepositoryDependency = Depends(ILogRepositoryDependency)
)-> ILogService:
    return LogService(
        log_repository = log_repository
    )

def IAdminLogServiceDependency(
    repository: IAdminLogRepository = Depends(IAdminLogRepositoryDependency),
) -> IAdminLogService:
    return AdminLogService(admin_log_repository=repository)
 