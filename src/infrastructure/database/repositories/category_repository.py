# src/infrastructure/database/repositories/category_repository.py
from typing import List

from sqlalchemy.orm import Session

from src.application.interfaces.repositories.category_repository_interface import ICategoryRepository
from src.domain.entities.categories.categories import Category
from src.infrastructure.database.models.categories.categories import CategoryModel
from src.infrastructure.database.utils.mapping import model_to_entity


class CategoryRepository(ICategoryRepository):
    def __init__(self, db: Session):
        self.db = db

    async def fetch_all_categories(self) -> List[Category]:
        db_categories = (
            self.db.query(CategoryModel)
            .order_by(CategoryModel.name.asc())
            .all()
        )
        return [model_to_entity(c, Category) for c in db_categories]