from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class UserBaseDTO(BaseModel):
    username: str = None
    email: str =None
    phone_number: str =None
    full_name: str =None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    premium_until: Optional[datetime] = None

class UserCreateDTO(UserBaseDTO):
    password: str

class UserUpdateDTO(UserBaseDTO):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_deleted: Optional[bool] = None
    premium_until: Optional[datetime] = None


class UserResponseDTO(UserBaseDTO):
    id: str

    # Quan trọng: Giúp Pydantic tự động đọc dữ liệu từ SQLAlchemy Model hoặc Entity
    model_config = ConfigDict(from_attributes=True)


class LoginDTO(BaseModel):
    email: str = None
    password: str = None

class ResponseLoginDTO(BaseModel):
    token: str