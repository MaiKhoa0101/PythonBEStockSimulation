from asyncio import Protocol


class IGetCollectionService(Protocol):
    async def get_all_collections(self, user_id: str):
        ...
class ICreateCollectionService(Protocol):
    async def create_favourite_list(self, user_id: str, movie_id: str):
        ...
class IAddMovieToCollectionService(Protocol):
    async def add_movie_to_collection(self, collection_id: str, user_id: str, movie_id: str):
        ...

class IDeleteCollectionService(Protocol):
    async def delete_favourite_list(self, favourite_list_id: str, user_id: str):
        ...