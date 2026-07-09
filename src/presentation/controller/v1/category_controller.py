# src/presentation/controller/category_controller.py
from fastapi import APIRouter, Depends

from src.application.interfaces.services.category_service_interface import IGetListCategoriesService
from src.presentation.controller.dependencies import IGetListCategoriesServiceDependency

router = APIRouter()


@router.get("/")
async def api_get_all_categories(
    getListCategoriesService: IGetListCategoriesService = Depends(IGetListCategoriesServiceDependency),
):
    result = await getListCategoriesService.get_all_categories()
    if result:
        return {"status": "Success", "data": result}
    return {"status": "Success", "data": []}