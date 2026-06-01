from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class User:
    id: str = None
    username: str =None
    email: str = None
    avatar: str = None
    password: str = None
    full_name: str = None   
    phone_number: str = None
    is_active: bool = True
    is_verified: bool = False
    is_deleted: bool = False
    premium_until: str = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

