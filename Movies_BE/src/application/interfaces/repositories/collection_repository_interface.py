from asyncio import Protocol


class ICollectionRepository (Protocol):
    def get_collection(self, user_id: str):
        ...
    def create_favourite_list(self, user_id: str, movie_id: str):
        ...

    def add_to_favourite_list(self, user_id: str, movie_id: str):
        ...

    def remove_from_favourite_list(self, user_id: str, movie_id: str):
        ...

    