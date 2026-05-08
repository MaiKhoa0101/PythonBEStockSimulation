from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime

# --- INPUT ---
class CreateCollectionDTO(BaseModel):
    name: str

class AddMovieToCollectionDTO(BaseModel):
    movie_id: str

# --- OUTPUT ---
class CollectionItemResponseDTO(BaseModel):
    movie_id: str
    added_at: datetime
    movie_name: str | None = None

    model_config = ConfigDict(from_attributes=True)

class CollectionResponseDTO(BaseModel):
    id: str
    name: str
    created_at: datetime
    items: List[CollectionItemResponseDTO] = [] 

    model_config = ConfigDict(from_attributes=True)