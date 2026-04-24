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
    
    # Các trường Audit có thể để trống (None) khi mới tạo
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Movie:
    id: str
    slug_name: str
    is_series: bool

    name: str = "Chưa có tên"
    description: Optional[str] = None
    episodes: List['Episode'] = field(default_factory=list) # Dùng ngoặc kép 'Episode' nếu Episode khai báo ở dưới, hoặc để trần nếu khai báo ở trên
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_valid_series(self) -> bool:
        """Logic kiểm tra: Nếu là phim bộ thì phải có nhiều hơn 1 tập"""
        if self.is_series and len(self.episodes) <= 1:
            return False
        return True