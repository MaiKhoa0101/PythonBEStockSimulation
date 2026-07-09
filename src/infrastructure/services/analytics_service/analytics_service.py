# src/infracstructure/services/analytics_service/analytics_service.py

from datetime import date
from typing import Optional

from src.application.interfaces.repositories.analytics_repository_interface import IAnalyticsRepository
from src.application.interfaces.services.analytics_service_interface import IAnalyticsService
from src.presentation.dtos.analytics_dto import (
    DistributionItem,
    DistributionResponse,
    TopTrendingItem,
    TopTrendingResponse,
    ViewsOverviewItem,
    ViewsOverviewResponse,
)


class AnalyticsService(IAnalyticsService):
    def __init__(self, repository: IAnalyticsRepository):
        self._repo = repository

    async def get_top_trending(
        self,
        start_date: Optional[date],
        end_date:   Optional[date],
        page:       int,
        size:       int,
    ) -> TopTrendingResponse:
        rows, total = self._repo.get_top_trending(start_date, end_date, page, size)
        total_pages = (total + size - 1) // size if size else 0

        return TopTrendingResponse(
            page=page,
            size=size,
            total=total,
            total_pages=total_pages,
            items=[
                TopTrendingItem(
                    movie_id=r["movie_id"],
                    movie_title=r.get("movie_title"),
                    views_count=r["views_count"],
                    likes_count=r["likes_count"],
                    click_count=r["click_count"],
                )
                for r in rows
            ],
        )

    async def get_views_overview(
        self,
        start_date:  Optional[date],
        end_date:    Optional[date],
        granularity: str = "day",
    ) -> ViewsOverviewResponse:
        """
        `granularity`: "minute" | "hour" | "day" | "week" | "month" — dùng cho
        trục thời gian của chart đường/miền bên FE. Repository sẽ raise
        ValueError nếu giá trị không hợp lệ (controller nên chặn từ trước
        bằng kiểu Literal, xem analytics_controller.py).
        """
        rows = self._repo.get_views_overview(start_date, end_date, granularity)

        return ViewsOverviewResponse(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            items=[
                ViewsOverviewItem(
                    date=r["date"],
                    total_views=r["total_views"],
                    total_likes=r["total_likes"],
                    total_clicks=r["total_clicks"],
                )
                for r in rows
            ],
        )

    async def get_genres_distribution(self) -> DistributionResponse:
        rows = self._repo.get_genres_distribution()

        total = sum(r["value"] for r in rows) or 1 
        return DistributionResponse(
            total_movies=total,
            items=[
                DistributionItem(
                    label=r["label"],
                    value=r["value"],
                    percent=round(r["value"] / total * 100, 2),
                )
                for r in rows
            ],
        )