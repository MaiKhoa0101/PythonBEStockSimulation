
from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
class MovieModel(Base):
    __tablename__ = "movie"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50))
    slug_name = Column(String(50))
    is_series = Column(Boolean, default=False)
    description = Column(String(1000))
    is_deleted = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50))
        
    episodes = relationship("EpisodeModel", back_populates="movie")
    favourited_by = relationship("FavouriteListModel", back_populates="movie")


class EpisodeModel(Base):
    __tablename__ = "episode"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Khai báo khóa ngoại trỏ về cột id của bảng movie
    id_movie = Column(String(50), ForeignKey("movie.id"))
    link_video = Column(String(100))
    name_episode = Column(String(50))
    description = Column(String(100))
    # Audit Fields
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50))

    movie = relationship("MovieModel", back_populates="episodes")
