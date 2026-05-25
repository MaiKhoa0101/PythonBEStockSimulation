

from src.application.interfaces.repositories.users_repository_interface import IUserRepository
from src.application.interfaces.services.users_service_interface import IGetUserById


class GetUserById (IGetUserById):
    def __init__(self,user_repository:IUserRepository):
        self.user_repository=user_repository
    async def get_user_by_id(self,user_id):
        return await self.user_repository.get_user_by_id(user_id)