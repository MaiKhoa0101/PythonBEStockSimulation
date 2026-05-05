from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class UserBaseDTO(BaseModel):
    username: str
    email: str
    phone_number: str
    full_name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserCreateDTO(UserBaseDTO):
    password: str

class UserUpdateDTO(UserBaseDTO):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_deleted: Optional[bool] = None

class UserResponseDTO(UserBaseDTO):
    id: str

    # Quan trọng: Giúp Pydantic tự động đọc dữ liệu từ SQLAlchemy Model hoặc Entity
    model_config = ConfigDict(from_attributes=True)
