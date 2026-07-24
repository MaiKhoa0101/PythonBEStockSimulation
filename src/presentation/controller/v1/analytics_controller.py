# src/presentation/controller/analytics_controller.py

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder

from src.infrastructure.services.logs.admin_log_service import write_audit_log
from src.application.interfaces.services.analytics_service_interface import IAnalyticsService
from src.infrastructure.security.author import RoleChecker
from src.presentation.controller.dependencies import IAnalyticsServiceDependency
from src.presentation.dtos.analytics_dto import (
    DistributionResponse,
    TopTrendingResponse,
    ViewsOverviewResponse,
)

router = APIRouter()
require_admin = RoleChecker(["admin"])

# Khớp với Granularity ở analytics_repository.py — nếu đổi 1 nơi thì đổi cả 2.
Granularity = Literal["minute", "hour", "day", "week", "month"]


@router.get(
    "/movies/top-trending",
    response_model=TopTrendingResponse,
    summary="Chart Cột — Top phim theo lượt xem",
)
async def api_top_trending(
    current_user_id: str = Depends(require_admin.check),
    start_date: Optional[date] = Query(None, description="Lọc từ ngày (vd: 2026-01-01)"),
    end_date:   Optional[date] = Query(None, description="Lọc đến ngày (vd: 2026-07-06)"),
    page:       int            = Query(1,    ge=1),
    size:       int            = Query(10,   ge=1, le=100),
    _:          str            = Depends(require_admin.check),
    service:    IAnalyticsService = Depends(IAnalyticsServiceDependency),
):
    write_audit_log(
        action="VIEW_TOP_TRENDING",
        admin_id=current_user_id,
        movie_id="N/A",
        movie_title="N/A",
        new_values={"startDate": start_date, "endDate": end_date, "granularity": ""},
    )
    return await service.get_top_trending(start_date, end_date, page, size)


@router.get(
    "/movies/views-overview",
    response_model=ViewsOverviewResponse,
    summary="Chart Đường / Miền — Xu hướng theo thời gian",
)
async def api_views_overview(
    current_user_id: str = Depends(require_admin.check),
    start_date:  Optional[date] = Query(None, description="Lọc từ ngày (vd: 2026-01-01)"),
    end_date:    Optional[date] = Query(None, description="Lọc đến ngày (vd: 2026-07-06)"),
    granularity: Granularity    = Query(
        "day",
        description="Mức gom nhóm trục thời gian cho chart. Dữ liệu gốc lưu theo bucket giờ "
                     "nên chọn 'minute' sẽ không mịn hơn 'hour'.",
    ),
    _:          str              = Depends(require_admin.check),
    service:    IAnalyticsService = Depends(IAnalyticsServiceDependency),
):
    write_audit_log(
        action="VIEW_MOVIE_OVERVIEW",
        admin_id=current_user_id,
        movie_id="N/A",
        movie_title="N/A",
        new_values={"startDate": start_date, "endDate": end_date, "granularity": granularity},
    )
    return await service.get_views_overview(start_date, end_date, granularity)


@router.get(
    "/movies/genres-distribution",
    response_model=DistributionResponse,
    summary="Chart Tròn — Cơ cấu thể loại phim",
)
async def api_genres_distribution(
    _:       str              = Depends(require_admin.check),
    service: IAnalyticsService = Depends(IAnalyticsServiceDependency),
):
    return await service.get_genres_distribution()



@router.get("/user-subscription-trends")
async def api_get_user_subscription_trends(
    startDate: str = Query(..., description="Ngày bắt đầu, định dạng YYYY-MM-DD"),
    endDate: str = Query(..., description="Ngày kết thúc, định dạng YYYY-MM-DD"),
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    current_user_id: str = Depends(require_admin.check),
    service: IAnalyticsService = Depends(IAnalyticsServiceDependency),
):
    result = await service.get_user_subscription_trends(startDate, endDate, granularity)

    write_audit_log(
        action="VIEW_SUBSCRIPTION",
        admin_id=current_user_id,
        movie_id="N/A",
        movie_title="user-subscription-trends",
        new_values={"startDate": startDate, "endDate": endDate, "granularity": granularity},
    )

    return {"status": "Success", "data": jsonable_encoder(result)}