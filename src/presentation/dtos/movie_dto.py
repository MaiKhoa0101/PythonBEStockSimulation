from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# ==========================================
# 1. EPISODE DTOs
# ==========================================

# 1.1 Base: Các trường chung nhất
class EpisodeBaseDTO(BaseModel):
    name_episode: str
    link_video: Optional[str] = None
    description: Optional[str] = None

# 1.2 Create: Dùng khi người dùng gọi API tạo tập phim mới
class EpisodeCreateDTO(EpisodeBaseDTO):
    name_episode: str
    link_video: Optional[str] = None
    description: Optional[str] = None

# 1.3 Response: Dùng khi trả dữ liệu tập phim về cho Client
class EpisodeResponseDTO(EpisodeBaseDTO):
    id: str
    id_movie: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Quan trọng: Giúp Pydantic tự động đọc dữ liệu từ SQLAlchemy Model hoặc Entity
    model_config = ConfigDict(from_attributes=True) 


# ==========================================
# 2. MOVIE DTOs
# ==========================================
class MovieBaseDTO(BaseModel):
    name: str
    slug_name: str
    is_series: bool = False
    description: Optional[str] = None
    poster_url: Optional[str] = None 

class MovieCreateDTO(MovieBaseDTO):
    episodes: List[EpisodeCreateDTO] = []

class MovieUpdateDTO(MovieBaseDTO):
    episodes: List[EpisodeCreateDTO] = []

class MoviePatchDTO(MovieBaseDTO):
    name: Optional[str] = None
    slug_name: Optional[str] = None
    is_series: Optional[bool] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None # [THÊM MỚI]
    episodes: Optional[List[EpisodeCreateDTO]] = None

class MovieResponseDTO(MovieBaseDTO):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class MovieDetailResponseDTO(MovieResponseDTO):
    episodes: List[EpisodeResponseDTO] = []