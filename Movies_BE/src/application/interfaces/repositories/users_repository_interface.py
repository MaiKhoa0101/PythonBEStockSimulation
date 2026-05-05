from typing import Protocol, Any
from src.domain.entities.users.user import User

class IUserRepository(Protocol):
    async def create_user(user_data: User) -> User:
        ...

    async def get_user_by_id(user_id: str) -> User:
        ...

    async def get_user_by_email(email: str) -> User:
        ...

    async def update_user(user_id: str, user_data: User) -> User:
        ...

    async def delete_user(user_id: str) -> None:
        ...