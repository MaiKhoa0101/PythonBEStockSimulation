
from sqlite3 import IntegrityError

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

    def create_movie_collection(self, user_id: str, name: str) -> CollectionEntity:
        new_collection = CollectionModel(
            user_id=user_id,
            name=name
        )
        self.db.add(new_collection)
        
        try:
            self.db.commit()
            self.db.refresh(new_collection) # Lấy data mới nhất (gồm cả ID vừa tự sinh) từ DB lên
            
            # Trả về Entity để Service xử lý tiếp
            return CollectionEntity(
                id=new_collection.id,
                user_id=new_collection.user_id,
                name=new_collection.name,
                created_at=new_collection.created_at,
                items=[] # List mới tạo dĩ nhiên chưa có phim nào
            )
        except Exception as e:
            self.db.rollback() # Quay xe nếu có lỗi
            raise e

    def add_to_movie_collection(self, collection_id: str, movie_id: str) -> bool:
        new_item = CollectionItemModel(
            collection_id=collection_id,
            movie_id=movie_id
        )
        self.db.add(new_item)
        
        try:
            self.db.commit()
            return True
        except IntegrityError:
            self.db.rollback() 
            return False

    def remove_from_movie_collection(self, collection_id: str, movie_id: str) -> bool:
        # Tìm xem cái dòng đó có tồn tại không
        item_to_delete = self.db.query(CollectionItemModel).filter(
            CollectionItemModel.collection_id == collection_id,
            CollectionItemModel.movie_id == movie_id
        ).first()

        if item_to_delete:
            self.db.delete(item_to_delete)
            self.db.commit()
            return True
        
        return False
        