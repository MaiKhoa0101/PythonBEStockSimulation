# src/application/interfaces/repositories/category_repository_interface.py
from abc import ABC, abstractmethod
from typing import List

from src.domain.entities.categories.categories import Category


class ICategoryRepository(ABC):
    @abstractmethod
    async def fetch_all_categories(self) -> List[Category]:
        ...