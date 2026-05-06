from fastapi import APIRouter, Depends, Path

from src.application.interfaces.services.collection_service_interface import IGetCollectionService
from src.presentation.controller.dependencies import IGetCollectionServiceDependency
from src.infrastructure.security.security import get_current_user_id
from src.presentation.dtos.movie_collection_dto import CreateCollectionDTO


router = APIRouter()

# Tạo danh sách mới
@router.post("/create")
async def create_new_collection(
    # collection_data: CreateCollectionDTO
    current_user_id: str = Depends(get_current_user_id) # Bắt buộc đăng nhập
):
    result = None
    if result:
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Lấy danh sách không thành công"
        }


# Lấy tất cả danh sách
@router.get("/my-collections")
async def get_my_collections(
    current_user_id: str = Depends(get_current_user_id),
    collection_service: IGetCollectionService = Depends(IGetCollectionServiceDependency)
):
    result = collection_service.get_all_collections(user_id=current_user_id,)
    if result:
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Lấy danh sách không thành công"
        }

@router.post("/{collection_id}/movies/{movie_id}")
async def add_movie_to_collection(
    collection_id: str = Path(...),
    movie_id: str = Path(...),
    current_user_id: str = Depends(get_current_user_id)
):
    pass