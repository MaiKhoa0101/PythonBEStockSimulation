from datetime import date
from typing import List, Literal, Optional, Protocol, Tuple

Granularity = Literal["minute", "hour", "day", "week", "month"]


class IAnalyticsRepository(Protocol):
    def get_top_trending(
        self,
        start_date: Optional[date],
        end_date:   Optional[date],
        page:       int,
        size:       int,
    ) -> Tuple[List[dict], int]:
        ...

    def get_views_overview(
        self,
        start_date:  Optional[date],
        end_date:    Optional[date],
        granularity: Granularity = "day",
    ) -> List[dict]:
        ...

    def get_genres_distribution(self) -> List[dict]:
        ...
    def fetch_user_subscription_trends(
        self,
        start_date:  Optional[date],
        end_date:    Optional[date],
        granularity: Granularity = "day",
    ) -> List[dict]:
        ...