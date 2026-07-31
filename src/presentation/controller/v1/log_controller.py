from datetime import datetime, timezone
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.infrastructure.database.redis import get_redis_client
from src.infrastructure.security.security import get_optional_user_id
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
    created_from: Optional[datetime] = Query(None, description="Lọc created_at >= (ISO 8601)"),
    created_to: Optional[datetime] = Query(None, description="Lọc created_at <= (ISO 8601)"),
    updated_from: Optional[datetime] = Query(None, description="Lọc updated_at >= (ISO 8601)"),
    updated_to: Optional[datetime] = Query(None, description="Lọc updated_at <= (ISO 8601)"),
    current_user_id: str = Depends(require_admin.check),
    logService: ILogService = Depends(ILogServiceDependency),
):
    if created_from and created_to and created_from > created_to:
        raise HTTPException(status_code=400, detail="created_from phải trước created_to")
    if updated_from and updated_to and updated_from > updated_to:
        raise HTTPException(status_code=400, detail="updated_from phải trước updated_to")

    result = await logService.fetch_list(
        page=page, size=size, status=status, name=name,
        created_from=created_from, created_to=created_to,
        updated_from=updated_from, updated_to=updated_to,
    )
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


VIEW_BUFFER_KEY = "buffer:movie_views"

class LogViewBody(BaseModel):
    episode_id: Optional[str] = None
    duration_watched: int = 0

@router.post("/log-view/{movie_id}")
async def api_log_movie_view(
    movie_id: str,
    body: LogViewBody,
    current_user_id: str = Depends(get_optional_user_id),
    redis=Depends(get_redis_client),
):
    payload = {
        "user_id": current_user_id,
        "movie_id": movie_id,
        "episode_id": body.episode_id,
        "duration_watched": body.duration_watched,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await redis.rpush(VIEW_BUFFER_KEY, json.dumps(payload))
    return {"status": "success", "message": "View logged to buffer"}