from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class User:
    id: str
    username: str
    email: str
    password: str
    full_name: str
    phone_number: str
    is_active: bool = True
    is_verified: bool = False
    is_deleted: bool = False
    premium_until: str = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

