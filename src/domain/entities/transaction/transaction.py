from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Transaction:
    id: str =None
    user_id: str = None
    package_id: str =None
    amount: int =None
    status: str =None
    payment_method: str =None
    created_at: Optional[datetime] = None
    