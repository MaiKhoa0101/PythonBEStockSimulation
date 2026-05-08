from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Episode:
    id: str
    id_movie: str
    name_episode: str
    link_video: Optional[str] = None
    description: Optional[str] = None
    is_deleted: bool = False

    # Các trường Audit có thể để trống (None) khi mới tạo
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Movie:
    id: str = None
    slug_name: str = None
    is_series: bool = None
    name: str = None
    description: Optional[str] = None
    poster_url: Optional[str] = None # [THÊM MỚI]
    episodes: List['Episode'] = field(default_factory=list) 
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    
    def is_valid_series(self) -> bool:
        if self.is_series and len(self.episodes) <= 1:
            return False
        return True