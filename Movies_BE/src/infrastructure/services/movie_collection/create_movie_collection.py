

from src.domain.entities.movie_collection.collection import CollectionEntity
from src.application.interfaces.services.collection_service_interface import ICreateCollectionService
from src.application.interfaces.repositories.collection_repository_interface import ICollectionRepository


class CreateMovieCollection(ICreateCollectionService):
    def __init__(self, collection_repository: ICollectionRepository):
        self.collection_repository = collection_repository

    async def create_collection(self, user_id: str, name: str):
        # Gọi Repository để tạo list mới
        result: CollectionEntity = self.collection_repository.create_movie_collection(user_id=user_id, name=name)
        
        if result:
            return {
                "collection_id": result.id,
                "name": result.name,
                "created_at": result.created_at,
                "items": result.items
            }
        else:
            return None
        
