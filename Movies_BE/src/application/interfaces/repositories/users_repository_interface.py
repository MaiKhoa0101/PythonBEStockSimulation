from typing import Protocol, Any

class IUserRepository(Protocol):
    async def create_user(user_data: Any) -> Any:
        ...

    async def get_user_by_id(user_id: str) -> Any:
        ...

    async def get_user_by_email(email: str) -> Any:
        ...

    async def update_user(user_id: str, user_data: Any) -> Any:
        ...

    async def delete_user(user_id: str) -> None:
        ...