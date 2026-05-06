
from src.domain.entities.movie_collection.collection import CollectionEntity, CollectionItemEntity
from src.infrastructure.database.models.movie_collection.movie_collection_model import CollectionItemModel, CollectionModel
from src.application.interfaces.repositories.collection_repository_interface import ICollectionRepository
from sqlalchemy.orm import Session, selectinload


class CollectionRepository(ICollectionRepository):
    def __init__(self, db:Session):
        self.db = db

    def get_collection(self, user_id: str):
        # 1. Truy vấn dữ liệu từ DB, đính kèm luôn các Items và thông tin Movie
        db_collections = self.db.query(CollectionModel).filter(
            CollectionModel.user_id == user_id
        ).options(
            selectinload(CollectionModel.items).selectinload(CollectionItemModel.movie)
        ).all()
        print("đi toi day 1")

        # 2. Ánh xạ (Mapping) từ Model (SQLAlchemy) sang Entity (Dataclass)
        result = []
        for db_collection in db_collections:
            # Chuyển đổi mảng items trước
            items_entity_list = []
            for item in db_collection.items:
                items_entity_list.append(
                    CollectionItemEntity(
                        collection_id=item.collection_id,
                        movie_id=item.movie_id,
                        added_at=item.added_at,
                        # Lấy tên phim từ bảng Movie nối sang, phòng hờ trường hợp bị null
                        movie_name=item.movie.name if item.movie else None 
                    )
                )
            
            # Đóng gói thành CollectionEntity hoàn chỉnh
            collection_entity = CollectionEntity(
                id=db_collection.id,
                user_id=db_collection.user_id,
                name=db_collection.name,
                created_at=db_collection.created_at,
                items=items_entity_list
            )
            result.append(collection_entity)
        print("ddi toi day 2")

        return result



    def create_favourite_list(self, user_id: int, movie_id: int):
        ...
    def add_to_favourite_list(self, user_id: int, movie_id: int):
        ...
    def remove_from_favourite_list(self, user_id: int, movie_id: int):
        ...
        