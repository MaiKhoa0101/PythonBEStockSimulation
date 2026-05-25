import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String,Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.infrastructure.database.session import Base

class ShortModel(Base):
    __tablename__= "shorts"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    movie_id = Column(String(50), ForeignKey("movie.id", ondelete="CASCADE"), nullable=False)
    episode_id = Column(String(50), ForeignKey("episode.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(50), ForeignKey("user.id"), nullable=False)

    title = Column(String(1000), nullable= False)
    slug = Column(String (200), unique= True, index= True)

    start_time = Column(Integer, nullable= True)
    duration = Column(Integer, nullable= True)

    video_url = Column(String(500), nullable=False)

    like_count = Column(Integer, default= 0)
    view_count = Column(Integer, default= 0)
    
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    movie = relationship("MovieModel", back_populates="shorts")
    episode = relationship("EpisodeModel", back_populates="shorts")
    user = relationship ("UserModel", back_populates="shorts")
