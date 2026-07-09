# src/presentation/dtos/analytics_dto.py

from datetime import date, datetime
from typing import List, Literal

from pydantic import BaseModel, Field

# Khớp với Granularity ở analytics_repository_interface.py — 2 nơi định nghĩa
# riêng có chủ đích (presentation vs domain layer không nên phụ thuộc chéo),
# nếu đổi danh sách giá trị hợp lệ thì sửa cả 2 chỗ.
Granularity = Literal["minute", "hour", "day", "week", "month"]


class TopTrendingItem(BaseModel):
    movie_id:    str
    movie_title: str | None = None
    views_count: int = Field(ge=0)
    likes_count: int = Field(ge=0)
    click_count: int = Field(ge=0)

    model_config = {"from_attributes": True}


class TopTrendingResponse(BaseModel):
    page:        int
    size:        int
    total:       int
    total_pages: int
    items:       List[TopTrendingItem]


class ViewsOverviewItem(BaseModel):
    date:         datetime
    total_views:  int = Field(ge=0)
    total_likes:  int = Field(ge=0)
    total_clicks: int = Field(ge=0)

    model_config = {"from_attributes": True}


class ViewsOverviewResponse(BaseModel):
    start_date:  date | None
    end_date:    date | None
    granularity: Granularity = "day"
    items:       List[ViewsOverviewItem]


class DistributionItem(BaseModel):
    label:   str
    value:   int
    percent: float   

    model_config = {"from_attributes": True}


class DistributionResponse(BaseModel):
    total_movies: int
    items:        List[DistributionItem]