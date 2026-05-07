from asyncio import Protocol


class ICollectionRepository (Protocol):
    async def get_collection(self, user_id: str):
        ...
    async def create_movie_collection(self, user_id: str, movie_id: str):
        ...

    async def add_to_movie_collection(self, user_id: str, movie_id: str):
        ...

    async def remove_from_movie_collection(self, user_id: str, movie_id: str):
        ...

    