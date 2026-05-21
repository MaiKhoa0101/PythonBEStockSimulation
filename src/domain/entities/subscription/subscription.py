from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Subscription:
    id: str
    name: str
    price: int
    duration_days: int
    description: str
    created_at: Optional[datetime] = None


