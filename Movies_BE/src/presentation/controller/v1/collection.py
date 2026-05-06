from fastapi import APIRouter, Depends, Path

from src.application.interfaces.services.collection_service_interface import IAddMovieToCollectionService, ICreateCollectionService, IGetCollectionService
from src.presentation.controller.dependencies import IAddMovieToCollectionServiceDependency, ICreateCollectionServiceDependency, IGetCollectionServiceDependency
from src.infrastructure.security.security import get_current_user_id
from src.presentation.dtos.movie_collection_dto import CreateCollectionDTO


router = APIRouter()

# 1. TẠO DANH SÁCH MỚI
@router.post("/create")
async def create_new_collection(
    collection_data: CreateCollectionDTO, # [ĐÃ SỬA]: Bổ sung dấu phẩy bị thiếu
    current_user_id: str = Depends(get_current_user_id),
    
    # [ĐÃ SỬA]: Tiêm Service vào để xử lý thay vì gán result = None
    collection_service: ICreateCollectionService = Depends(ICreateCollectionServiceDependency) 
):
    # Gọi service tạo list (nhớ dùng await)
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
        # [ĐÃ SỬA]: Đổi câu thông báo lỗi cho khớp với hành động Tạo
        return {
            "status": "Failed",
            "data": "Tạo danh sách mới không thành công" 
        }

# 2. LẤY TẤT CẢ DANH SÁCH
@router.get("/my-collections")
async def get_my_collections(
    current_user_id: str = Depends(get_current_user_id),
    collection_service: IGetCollectionService = Depends(IGetCollectionServiceDependency)
):
    # [ĐÃ SỬA LỖI NGHIÊM TRỌNG]: Phải có "await" khi gọi service chạm vào Database
    # [ĐÃ SỬA]: Bỏ dấu phẩy dư thừa ở cuối tham số user_id
    result = await collection_service.get_all_collections(user_id=current_user_id) 
    
    if result is not None: # Có thể user chưa tạo list nào (list rỗng []) vẫn tính là thành công
        return {
            "status": "Success",
            "data": result
        }
    else: 
        return {
            "status": "Failed",
            "data": "Lấy danh sách không thành công"
        }

# 3. THÊM PHIM VÀO DANH SÁCH
@router.post("/{collection_id}/movies/{movie_id}")
async def add_movie_to_collection(
    collection_id: str = Path(...),
    movie_id: str = Path(...),
    current_user_id: str = Depends(get_current_user_id),
    collection_item_service: IAddMovieToCollectionService = Depends(IAddMovieToCollectionServiceDependency)
):
    # Truyền cả 3 ID xuống cho Service. 
    # (Vì Service cần current_user_id để kiểm tra xem ông user này có phải là chủ của collection kia không)
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
        # Nếu service trả về False (do trùng phim, hoặc list không thuộc về user)
        return {
            "status": "Failed",
            "data": "Không thể thêm phim (Phim đã có sẵn hoặc bạn không có quyền)"
        }