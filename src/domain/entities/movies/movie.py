from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from domain.entities.actors.actor import Actor
from domain.entities.categories.categories import Category
from domain.entities.country.country import Country
from domain.entities.directors.director import Director
from domain.entities.imdb.imdb import MovieExternalIds



@dataclass
class Episode:
    id: str
    id_movie: str
    name_episode: str
    slug: Optional[str] = None
    filename: Optional[str] = None
    link_embed: Optional[str] = None
    link_m3u8: Optional[str] = None
    server_name: Optional[str] = None
    description: Optional[str] = None
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Movie:
    id: str = None
    name: str = None
    slug_name: str = None
    origin_name: Optional[str] = None
    is_series: bool = False

    # Trạng thái: "completed" | "ongoing" | ...
    status: Optional[str] = None

    description: Optional[str] = None
    poster_url: Optional[str] = None
    thumb_url: Optional[str] = None
    trailer_url: Optional[str] = None

    # Thông tin phát sóng
    quality: Optional[str] = None      # FHD, HD, CAM, ...
    lang: Optional[str] = None         # Vietsub, Thuyết Minh, ...
    time: Optional[str] = None         # "174 phút"
    year: Optional[int] = None
    view: int = 0

    episode_current: Optional[str] = None   # "Full" | "Tập 12" | ...
    episode_total: Optional[str] = None     # "1" | "24" | ...

    is_copyright: bool = False
    sub_docquyen: bool = False
    chieurap: bool = False
    notify: Optional[str] = None
    showtimes: Optional[str] = None

    # Relations
    episodes: List['Episode'] = field(default_factory=list)
    actors: List['Actor'] = field(default_factory=list)
    directors: List['Director'] = field(default_factory=list)
    categories: List['Category'] = field(default_factory=list)
    countries: List['Country'] = field(default_factory=list)
    external_ids: Optional['MovieExternalIds'] = None

    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_valid_series(self) -> bool:
        if self.is_series and len(self.episodes) <= 1:
            return False
        return True