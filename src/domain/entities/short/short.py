from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Short:
    id:str = None
    movie_id:str =None
    user_id:str = None
    episode_id:str =None
    title:str = None
    slug:str = None
    start_time: int =None
    duration:int =None
    video_url:str = None

    like_count:int = 0
    view_count:int = 0

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
