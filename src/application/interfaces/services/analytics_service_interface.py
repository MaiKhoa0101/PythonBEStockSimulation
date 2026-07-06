# src/application/services/analytics_service.py

from asyncio import Protocol
from datetime import date
from typing import Optional

from src.presentation.dtos.analytics_dto import (
    DistributionItem,
    DistributionResponse,
    TopTrendingItem,
    TopTrendingResponse,
    ViewsOverviewItem,
    ViewsOverviewResponse,
)


class IAnalyticsService(Protocol):
    async def get_top_trending(
        start_date: Optional[date],
        end_date:   Optional[date],
        page:       int,
        size:       int,
    ) -> TopTrendingResponse:
       ...

    async def get_views_overview(
        start_date: Optional[date],
        end_date:   Optional[date],
    ) -> ViewsOverviewResponse:
        ...

    async def get_genres_distribution():
        ...