from src.domain.entities.short.short import Short
from src.infrastructure.database.utils.mapping import dto_to_entity
from src.presentation.dtos.short_dto import ShortCreateDTO
from src.application.interfaces.repositories.short_repository_interface import IShortRepository
from src.application.interfaces.services.short_service_interface import IShortService


class ShortService(IShortService):
    def __init__(self, short_repository: IShortRepository):
        self.short_repository= short_repository

    async def get_shorts (self, id_user:str = None):
        return await self.short_repository.get_shorts(id_user)

    async def get_shorts_by_user_id(self,id:str):
        result = await self.short_repository.get_shorts_by_user_id(id)
        return result

    async def get_shorts_by_movie_id(self,id:str):
        result = await self.short_repository.get_shorts_by_movie_id(id)
        return result

    async def get_shorts_by_episode_id(self,id:str):
        result = await self.short_repository.get_shorts_by_episode_id(id)
        return result

    async def get_short_by_self_id(self,id:str):
        result = await self.short_repository.get_short_by_self_id(id)
        return result

    async def create_short(self,short_create_DTO:ShortCreateDTO):
        short = dto_to_entity(
            short_create_DTO,
            Short
        )
        result = await self.short_repository.create_short(short)
        return result
    
    async def delete_short(self,id:str):
        result =  await self.short_repository.delete_short(id)
        return result

