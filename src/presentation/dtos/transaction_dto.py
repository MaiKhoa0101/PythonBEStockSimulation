


from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class TransactionBaseDTO(BaseModel):
    user_id: str
    package_id: str
    amount: int
    payment_method: str


class TransactionCreateDTO(TransactionBaseDTO):
    status: str = "Pending"
    payment_method:str = "Credit Card"
    pass

class TransactionResponseDTO(TransactionBaseDTO):
    id: str = None
    user_id: str = None
    package_id: str = None
    amount: int = None
    status: str = "Pending"
    payment_method: str = None
    created_at: Optional[datetime] = None


