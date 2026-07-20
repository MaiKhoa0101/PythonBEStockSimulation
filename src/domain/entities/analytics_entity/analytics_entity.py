from dataclasses import dataclass
from datetime import date as date_type


@dataclass(frozen=True)
class UserSubTrendPoint:

    bucket_date: date_type
    new_users: int
    new_subscriptions: int
    unsubscriptions: int