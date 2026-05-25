from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ShortBaseDTO(BaseModel):
    movie_id:str
    user_id:str
    episode_id:str
    title:str
    slug:str
    start_time: int =None
    duration:int =None
    video_url:str =None

    like_count:int = 0
    view_count:int = 0

class ShortCreateDTO(ShortBaseDTO):
    pass

class ShortResponseDTO(ShortBaseDTO):
    id:str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None