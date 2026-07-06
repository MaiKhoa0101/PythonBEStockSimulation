# src/presentation/controller/analytics_controller.py

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

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


@router.get(
    "/movies/top-trending",
    response_model=TopTrendingResponse,
    summary="Chart Cột — Top phim theo lượt xem",
)
async def api_top_trending(
    start_date: Optional[date] = Query(None, description="Lọc từ ngày (vd: 2026-01-01)"),
    end_date:   Optional[date] = Query(None, description="Lọc đến ngày (vd: 2026-07-06)"),
    page:       int            = Query(1,    ge=1),
    size:       int            = Query(10,   ge=1, le=100),
    _:          str            = Depends(require_admin.check),
    service:    IAnalyticsService = Depends(IAnalyticsServiceDependency),
):
    return await service.get_top_trending(start_date, end_date, page, size)


@router.get(
    "/movies/views-overview",
    response_model=ViewsOverviewResponse,
    summary="Chart Đường / Miền — Xu hướng theo thời gian",
)
async def api_views_overview(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
    _:          str            = Depends(require_admin.check),
    service:    IAnalyticsService = Depends(IAnalyticsServiceDependency),
):
    return await service.get_views_overview(start_date, end_date)


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