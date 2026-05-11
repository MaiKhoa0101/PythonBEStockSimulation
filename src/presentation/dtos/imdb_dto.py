from pydantic import BaseModel, ConfigDict
from typing import Optional

class TmdbInfoDTO(BaseModel):
    type: Optional[str] = None
    id: Optional[str] = None
    season: Optional[int] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None

class ImdbInfoDTO(BaseModel):
    id: Optional[str] = None

class MovieExternalIdsCreateDTO(BaseModel):
    tmdb_type: Optional[str] = None
    tmdb_id: Optional[str] = None
    tmdb_season: Optional[int] = None
    tmdb_vote_average: Optional[float] = None
    tmdb_vote_count: Optional[int] = None
    imdb_id: Optional[str] = None

class MovieExternalIdsResponseDTO(MovieExternalIdsCreateDTO):
    id: str
    id_movie: str
    model_config = ConfigDict(from_attributes=True)