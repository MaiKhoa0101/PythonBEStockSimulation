from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class User:
    id: str
    email: str
    password: str
    full_name: str
    is_active: bool = True
    is_verified: bool = False
    is_deleted: bool = False

    # Các trường Audit có thể để trống (None) khi mới tạo
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

