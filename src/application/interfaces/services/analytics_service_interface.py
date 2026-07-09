from datetime import date
from typing import Optional, Protocol

from src.presentation.dtos.analytics_dto import (
    DistributionResponse,
    Granularity,
    TopTrendingResponse,
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