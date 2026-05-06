
from src.application.interfaces.services.collection_service_interface import IAddMovieToCollectionService
from src.application.interfaces.repositories.collection_repository_interface import ICollectionRepository


class AddMovieToCollection(IAddMovieToCollectionService):
    def __init__(self, collection_repository: ICollectionRepository):
        self.collection_repository = collection_repository

    async def add_movie_to_collection(self, collection_id: str, user_id: str, movie_id: str):
        # Gọi Repository để thêm phim vào danh sách
        result = self.collection_repository.add_movie_to_collection(collection_id=collection_id, user_id=user_id, movie_id=movie_id)
        
        if result:
            return {
                "collection_id": result.collection_id,
                "user_id": result.user_id,
                "movie_id": result.movie_id
            }
        else:
            return None
        