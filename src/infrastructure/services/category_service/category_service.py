# src/infrastructure/services/categories/category_service.py
from typing import List


from src.application.interfaces.repositories.category_repository_interface import ICategoryRepository
from src.application.interfaces.services.category_service_interface import IGetListCategoriesService
from src.infrastructure.database.utils.mapping import entity_to_dto
from src.presentation.dtos.categories_dto import CategoryDTO


class GetListCategoriesService(IGetListCategoriesService):
    def __init__(self, repository: ICategoryRepository):
        self.category_repository = repository

    async def get_all_categories(self) -> List[CategoryDTO]:
        categories = await self.category_repository.fetch_all_categories()
        return [entity_to_dto(c, CategoryDTO) for c in categories]