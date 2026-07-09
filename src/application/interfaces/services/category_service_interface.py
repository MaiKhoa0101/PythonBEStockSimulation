# src/application/interfaces/services/category_service_interface.py
from abc import ABC, abstractmethod
from typing import List

from src.presentation.dtos.categories_dto import CategoryDTO


class IGetListCategoriesService(ABC):
    @abstractmethod
    async def get_all_categories(self) -> List[CategoryDTO]:
        ...