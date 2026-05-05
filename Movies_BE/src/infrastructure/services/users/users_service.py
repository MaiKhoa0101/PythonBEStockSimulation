
from src.application.interfaces.services.users_service_interface import IUserService


class UserService(IUserService):
    async def create_user(user_data: dict) -> dict:
        # Logic để tạo user mới
        pass

    async def get_user_by_id(user_id: str) -> dict:
        # Logic để lấy thông tin user theo ID
        pass

    async def get_user_by_email(email: str) -> dict:
        # Logic để lấy thông tin user theo email
        pass

    async def update_user(user_id: str, user_data: dict) -> dict:
        # Logic để cập nhật thông tin user
        pass

    async def delete_user(user_id: str) -> None:
        # Logic để xóa user
        pass