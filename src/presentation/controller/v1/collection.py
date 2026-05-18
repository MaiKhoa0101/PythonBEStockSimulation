from fastapi import APIRouter, Depends, Path

from src.application.interfaces.services.collection_service_interface import IAddMovieToCollectionService, ICreateCollectionService, IGetCollectionService
from src.presentation.controller.dependencies import IAddMovieToCollectionServiceDependency, ICreateCollectionServiceDependency, IGetCollectionServiceDependency
from src.infrastructure.security.security import get_current_user_id
from src.presentation.dtos.movie_collection_dto import CreateCollectionDTO


router = APIRouter()

# 1. TẠO DANH SÁCH MỚI
@router.post("/create")
async def create_new_collection(
    collection_data: CreateCollectionDTO,
    current_user_id: str = Depends(get_current_user_id),
    collection_service: ICreateCollectionService = Depends(ICreateCollectionServiceDependency) 
):
    result = await collection_service.create_collection(
        user_id=current_user_id, 
        name=collection_data.name
    )
    
    if result:
        return {
            "status": "Success",
            "data": result
        }
    else: 
        return {
            "status": "Failed",
            "data": "Tạo danh sách mới không thành công" 
        }

@router.get("/my-collections")
async def get_my_collections(
    current_user_id: str = Depends(get_current_user_id),
    collection_service: IGetCollectionService = Depends(IGetCollectionServiceDependency)
):
    result = await collection_service.get_all_collections(user_id=current_user_id) 
    
    if result is not None: 
        return {
            "status": "Success",
            "data": result
        }
    else: 
        return {
            "status": "Failed",
            "data": "Lấy danh sách không thành công"
        }

@router.post("/{collection_id}/movies/{movie_id}")
async def add_movie_to_collection(
    collection_id: str = Path(...),
    movie_id: str = Path(...),
    current_user_id: str = Depends(get_current_user_id),
    collection_item_service: IAddMovieToCollectionService = Depends(IAddMovieToCollectionServiceDependency)
):
    result = await collection_item_service.add_movie_to_list(
        user_id=current_user_id,
        collection_id=collection_id, 
        movie_id=movie_id
    )
    
    if result:
        return {
            "status": "Success",
            "data": "Đã thêm phim vào danh sách thành công"
        }
    else:
        return {
            "status": "Failed",
            "data": "Không thể thêm phim (Phim đã có sẵn hoặc bạn không có quyền)"
        }