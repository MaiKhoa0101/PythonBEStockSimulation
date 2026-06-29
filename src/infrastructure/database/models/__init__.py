# Gọi tên tất cả các Model để SQLAlchemy nạp chúng vào bộ nhớ cùng 1 lúc
from src.infrastructure.database.models.associations.associations import movie_actor_association, movie_category_association, movie_country_association, movie_director_association
from src.infrastructure.database.models.movies.movie_model import (
    MovieModel, 
    EpisodeModel
)
from src.infrastructure.database.models.actors.actors import ActorModel
from src.infrastructure.database.models.imdb.imdb import MovieExternalIdsModel
from src.infrastructure.database.models.directors.director import DirectorModel
from src.infrastructure.database.models.categories.categories import CategoryModel
from src.infrastructure.database.models.country.country import CountryModel
from src.infrastructure.database.models.celery_task_log.celery_task_log import CeleryTaskLog
from src.infrastructure.database.models.users.user_model import UserModel
from src.infrastructure.database.models.movie_collection.movie_collection_model import CollectionModel, CollectionItemModel
from src.infrastructure.database.models.subscription.subscription_model import SubscriptionPackageModel
from src.infrastructure.database.models.transaction.transaction_model import TransactionModel
from src.infrastructure.database.models.shorts.short_model import ShortModel
