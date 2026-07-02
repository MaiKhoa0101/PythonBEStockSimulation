from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.interfaces.services.log_service_interface import ILogService
from src.infrastructure.security.author import RoleChecker
from src.presentation.controller.dependencies import ILogServiceDependency

router = APIRouter()
require_admin = RoleChecker(["admin"])


@router.get("/")
async def api_get_log_list(
    page: int = Query(1, ge=1, description="Trang hiện tại, bắt đầu từ 1"),
    size: int = Query(20, ge=1, le=100, description="Số record mỗi trang, tối đa 100"),
    status: Optional[str] = Query(None, description="PENDING|STARTED|RETRY|SUCCESS|FAILURE"),
    name: Optional[str] = Query(None, description="Lọc theo tên task (tìm gần đúng)"),
    current_user_id: str = Depends(require_admin.check),
    logService: ILogService = Depends(ILogServiceDependency),
):
    result = await logService.fetch_list(page=page, size=size, status=status, name=name)
    if result:
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Lấy danh sách không thành công"}


@router.get("/summary")
async def api_get_log_status_summary(
    current_user_id: str = Depends(require_admin.check),
    logService: ILogService = Depends(ILogServiceDependency),
):
    """Đếm số lượng task theo từng trạng thái — phục vụ dashboard tổng quan."""
    result = await logService.fetch_status_summary()
    return {"status": "Success", "data": result}


@router.get("/{task_id}")
async def api_get_log_detail(
    task_id: str,
    current_user_id: str = Depends(require_admin.check),
    logService: ILogService = Depends(ILogServiceDependency),
):
    result = await logService.fetch_detail(task_id)
    if result:
        return {"status": "Success", "data": result}
    raise HTTPException(status_code=404, detail="Không tìm thấy task log")