


from src.infrastructure.database.utils.mapping import dto_to_entity
from src.domain.entities.users.user import User
from src.presentation.dtos.user_dto import UserUpdateDTO
from src.application.interfaces.repositories.users_repository_interface import IUserRepository
from src.application.interfaces.services.users_service_interface import IUpdateUser


class UpdateUser(IUpdateUser):
    def __init__ (self, user_repository:IUserRepository):
        self.user_repository=user_repository

    async def update_user(self,user_id:str, user_data:UserUpdateDTO):
        print("vao duoc service update")
        user_data = dto_to_entity(user_data,User)
        await self.user_repository.update_user(user_id,user_data)
