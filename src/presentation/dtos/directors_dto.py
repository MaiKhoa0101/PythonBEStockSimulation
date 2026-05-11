from pydantic import BaseModel, ConfigDict
from typing import Optional

class DirectorDTO(BaseModel):
    id: str
    name: str
    slug: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
