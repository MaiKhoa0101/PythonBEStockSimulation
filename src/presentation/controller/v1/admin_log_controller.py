from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.interfaces.services.admin_log_service_interface import IAdminLogService
from src.infrastructure.security.author import RoleChecker
from src.presentation.controller.dependencies import IAdminLogServiceDependency

router = APIRouter()
require_admin = RoleChecker(["admin"])


@router.get("/")
async def api_get_admin_log_list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None, description="CREATE | UPDATE | DELETE"),
    admin_id: Optional[str] = Query(None),
    movie_id: Optional[str] = Query(None),
    current_user_id: str = Depends(require_admin.check),
    service: IAdminLogService = Depends(IAdminLogServiceDependency),
):
    result = await service.fetch_list(
        page=page, size=size,
        action=action, admin_id=admin_id, movie_id=movie_id,
    )
    return {"status": "Success", "data": result}


@router.get("/summary")
async def api_get_admin_log_summary(
    current_user_id: str = Depends(require_admin.check),
    service: IAdminLogService = Depends(IAdminLogServiceDependency),
):
    result = await service.fetch_action_summary()
    return {"status": "Success", "data": result}


@router.get("/{log_id}")
async def api_get_admin_log_detail(
    log_id: str,
    current_user_id: str = Depends(require_admin.check),
    service: IAdminLogService = Depends(IAdminLogServiceDependency),
):
    result = await service.fetch_detail(log_id)
    if result:
        return {"status": "Success", "data": result}
    raise HTTPException(status_code=404, detail="Không tìm thấy audit log")