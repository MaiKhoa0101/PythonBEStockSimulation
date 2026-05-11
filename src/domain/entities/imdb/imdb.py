from dataclasses import dataclass, field
from typing import  Optional

@dataclass
class MovieExternalIds:
    id: str
    id_movie: str
    tmdb_type: Optional[str] = None
    tmdb_id: Optional[str] = None
    tmdb_season: Optional[int] = None
    tmdb_vote_average: Optional[float] = None
    tmdb_vote_count: Optional[int] = None
    imdb_id: Optional[str] = None
