from asyncio import Protocol
from datetime import date
from typing import Optional


class IAnalyticsRepository(Protocol):
    def get_top_trending(
        start_date: Optional[date],
        end_date:   Optional[date],
        page:       int,
        size:       int,
    ):
        ...

    def get_views_overview(
        start_date: Optional[date],
        end_date:   Optional[date],
    ):
        ...

    def get_top_trending(
        start_date: Optional[date],
        end_date:   Optional[date],
        page:       int,
        size:       int,
    ) :
        ...

    def get_views_overview(
        start_date: Optional[date],
        end_date:   Optional[date],
    ):
        ...
    
    def get_genres_distribution():
        ...

    