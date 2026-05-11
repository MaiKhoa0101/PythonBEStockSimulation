from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

from presentation.dtos.actors_dto import ActorDTO
from presentation.dtos.categories_dto import CategoryDTO
from presentation.dtos.country_dto import CountryDTO
from presentation.dtos.directors_dto import DirectorDTO
from presentation.dtos.imdb_dto import MovieExternalIdsCreateDTO, MovieExternalIdsResponseDTO


class EpisodeBaseDTO(BaseModel):
    name_episode: str
    slug: Optional[str] = None
    filename: Optional[str] = None
    link_embed: Optional[str] = None
    link_m3u8: Optional[str] = None
    server_name: Optional[str] = None
    description: Optional[str] = None


class EpisodeCreateDTO(EpisodeBaseDTO):
    pass


class EpisodeUpdateDTO(EpisodeBaseDTO):
    name_episode: Optional[str] = None


class EpisodeResponseDTO(EpisodeBaseDTO):
    id: str
    id_movie: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MovieBaseDTO(BaseModel):
    name: str
    slug_name: str
    origin_name: Optional[str] = None
    is_series: bool = False

    status: Optional[str] = None

    description: Optional[str] = None
    poster_url: Optional[str] = None
    thumb_url: Optional[str] = None
    trailer_url: Optional[str] = None

    quality: Optional[str] = None
    lang: Optional[str] = None
    time: Optional[str] = None
    year: Optional[int] = None
    view: int = 0

    episode_current: Optional[str] = None
    episode_total: Optional[str] = None

    is_copyright: bool = False
    sub_docquyen: bool = False
    chieurap: bool = False
    notify: Optional[str] = None
    showtimes: Optional[str] = None


class MovieCreateDTO(MovieBaseDTO):
    episodes: List[EpisodeCreateDTO] = []
    actor_ids: List[str] = []
    director_ids: List[str] = []
    category_ids: List[str] = []
    country_ids: List[str] = []
    external_ids: Optional[MovieExternalIdsCreateDTO] = None


class MovieUpdateDTO(MovieBaseDTO):
    episodes: List[EpisodeCreateDTO] = []
    actor_ids: List[str] = []
    director_ids: List[str] = []
    category_ids: List[str] = []
    country_ids: List[str] = []
    external_ids: Optional[MovieExternalIdsCreateDTO] = None


class MoviePatchDTO(BaseModel):
    name: Optional[str] = None
    slug_name: Optional[str] = None
    origin_name: Optional[str] = None
    is_series: Optional[bool] = None
    type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    thumb_url: Optional[str] = None
    trailer_url: Optional[str] = None
    quality: Optional[str] = None
    lang: Optional[str] = None
    time: Optional[str] = None
    year: Optional[int] = None
    view: Optional[int] = None
    episode_current: Optional[str] = None
    episode_total: Optional[str] = None
    is_copyright: Optional[bool] = None
    sub_docquyen: Optional[bool] = None
    chieurap: Optional[bool] = None
    notify: Optional[str] = None
    showtimes: Optional[str] = None
    episodes: Optional[List[EpisodeCreateDTO]] = None
    actor_ids: Optional[List[str]] = None
    director_ids: Optional[List[str]] = None
    category_ids: Optional[List[str]] = None
    country_ids: Optional[List[str]] = None
    external_ids: Optional[MovieExternalIdsCreateDTO] = None


class MovieResponseDTO(MovieBaseDTO):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    actors: List[ActorDTO] = []
    directors: List[DirectorDTO] = []
    categories: List[CategoryDTO] = []
    countries: List[CountryDTO] = []
    model_config = ConfigDict(from_attributes=True)


class MovieDetailResponseDTO(MovieResponseDTO):
    episodes: List[EpisodeResponseDTO] = []
    external_ids: Optional[MovieExternalIdsResponseDTO] = None