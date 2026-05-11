from pydantic import BaseModel, ConfigDict
from typing import Optional

class CategoryDTO(BaseModel):
    id: str
    name: str
    slug: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
