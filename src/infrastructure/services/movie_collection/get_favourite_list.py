

from fastapi import Depends

from src.application.interfaces.repositories.collection_repository_interface import ICollectionRepository
from src.application.interfaces.services.collection_service_interface import IGetCollectionService


class GetCollectionService(IGetCollectionService):
    def __init__(
        self, 
        collection_repository: ICollectionRepository
    ):
        self.collection_repository = collection_repository

    async def get_all_collections(self, user_id: int):
        result =  await self.collection_repository.get_collection(user_id)
        print("Vào được đây vowis ressult ", result)

        return result