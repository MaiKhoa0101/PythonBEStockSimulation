from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class CollectionItemEntity:
    collection_id: str
    movie_id: str
    added_at: Optional[datetime] = None
    
    # Optional: Có thể nhét thêm tên phim vào đây để truyền lên DTO
    movie_name: Optional[str] = None 

@dataclass
class CollectionEntity:
    id: str
    user_id: str
    name: str
    created_at: Optional[datetime] = None
    
    # Một danh sách chứa nhiều item bên trong
    items: List[CollectionItemEntity] = field(default_factory=list)