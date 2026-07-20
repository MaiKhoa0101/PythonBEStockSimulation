from datetime import date
from typing import Optional, Protocol

from src.presentation.dtos.analytics_dto import (
    DistributionResponse,
    Granularity,
    TopTrendingResponse,
    UserSubTrendsResponseDTO,
    ViewsOverviewResponse,
)


class IAnalyticsService(Protocol):
    async def get_top_trending(
        self,
        start_date: Optional[date],
        end_date:   Optional[date],
        page:       int,
        size:       int,
    ) -> TopTrendingResponse:
        ...

    async def get_views_overview(
        self,
        start_date:  Optional[date],
        end_date:    Optional[date],
        granularity: Granularity = "day",
    ) -> ViewsOverviewResponse:
        ...

    async def get_genres_distribution(self) -> DistributionResponse:
        ...

    async def get_user_subscription_trends(
        self, start_date: str, end_date: str, granularity: str
    ) -> UserSubTrendsResponseDTO:
        """Trả về xu hướng người dùng mới / đăng ký / hủy gói theo trục thời gian."""
        raise NotImplementedError
    
# src/application/interfaces/services/analytics_service_interface.py
