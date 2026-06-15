

from src.presentation.dtos.user_dto import UserResponseDTO
from src.infrastructure.database.utils.mapping import entity_to_dto
from src.application.interfaces.repositories.users_repository_interface import IUserRepository
from src.application.interfaces.services.users_service_interface import IGetUserById


class GetUserById (IGetUserById):
    def __init__(self,user_repository:IUserRepository):
        self.user_repository=user_repository
    async def get_user_by_id_for_self(self,user_id):
        response = await self.user_repository.get_user_by_id(user_id) 
        result = entity_to_dto(
            response,
            UserResponseDTO
        )
        print("k qua la get by id:",result)
        return result  
    async def get_user_by_id(self,user_id):
        response =  await self.user_repository.get_user_by_id(user_id)
        result = entity_to_dto(
            response,
            UserResponseDTO
        )
        return result  
