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

# 2.1 Base: Các trường chung nhất
class MovieBaseDTO(BaseModel):
    name: str
    slug_name: str
    is_series: bool = False
    description: Optional[str] = None

# 2.2 Create: Dùng khi người dùng gọi API tạo phim mới 
class MovieCreateDTO(MovieBaseDTO):
    name: str
    slug_name: str
    is_series: bool = False
    description: Optional[str] = None
    # Thêm dòng này để hứng mảng các tập phim:
    episodes: List[EpisodeCreateDTO] = []

# 2.3 Response: Dùng khi trả dữ liệu phim về cho Client
class MovieResponseDTO(MovieBaseDTO):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# 2.4 Detail Response: Trả về phim kèm theo danh sách các tập phim
class MovieDetailResponseDTO(MovieResponseDTO):
    # Lồng danh sách EpisodeResponseDTO vào trong Movie
    episodes: List[EpisodeResponseDTO] = []