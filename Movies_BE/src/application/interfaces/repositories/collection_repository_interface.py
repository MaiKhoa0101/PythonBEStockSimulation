from asyncio import Protocol


class ICollectionRepository (Protocol):
    def get_collection(self, user_id: str):
        ...
    def create_movie_collection(self, user_id: str, movie_id: str):
        ...

    def add_to_movie_collection(self, user_id: str, movie_id: str):
        ...

    def remove_from_movie_collection(self, user_id: str, movie_id: str):
        ...

    