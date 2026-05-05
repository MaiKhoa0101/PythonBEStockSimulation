from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class UserBaseDTO(BaseModel):
    username: str
    email: str
    phone_number: Optional[str] = None
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserCreateDTO(UserBaseDTO):
    password: str

class UserResponseDTO(UserBaseDTO):
    id: str

    # Quan trọng: Giúp Pydantic tự động đọc dữ liệu từ SQLAlchemy Model hoặc Entity
    model_config = ConfigDict(from_attributes=True)
