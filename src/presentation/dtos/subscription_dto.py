from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class SubsciptionBaseDTO(BaseModel):
    id:str
    name: str
    price: int
    duration_days: int
    description: str
    created_at: Optional[datetime] = None


class SubscriptionCreateDTO(SubsciptionBaseDTO):
    id:str = None

class SubscriptionUpdateDTO(SubsciptionBaseDTO):
    name: Optional[str] = None
    price: Optional[int] = None
    duration_days: Optional[int] = None
    description: Optional[str] = None