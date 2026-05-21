from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Transaction:
    id: str
    user_id: str
    package_id: str
    amount: int
    status: str
    created_at: Optional[datetime] = None

