from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, String, DateTime, ForeignKey,
    Integer, Float, Table
)
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.infrastructure.database.models.associations.associations import(
    movie_category_association, 
    movie_actor_association,
    movie_director_association,
    movie_country_association
)
import uuid

class EpisodeModel(Base):
    __tablename__ = "episode"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_movie = Column(String(50), ForeignKey("movie.id"), nullable=False)

    name_episode = Column(String(100))
    slug = Column(String(100))
    filename = Column(String(500))
    link_embed = Column(String(500))
    link_m3u8 = Column(String(500))
    server_name = Column(String(100))
    description = Column(String(500))

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_by = Column(String(50))


    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by = Column(String(50))

    movie = relationship("MovieModel", back_populates="episodes")
    shorts= relationship("ShortModel", back_populates="episode", cascade="all, delete-orphan")


class MovieModel(Base):
    __tablename__ = "movie"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200))
    slug_name = Column(String(200), unique=True, index=True)
    origin_name = Column(String(250))
    is_series = Column(Boolean, default=False)

    status = Column(String(50))     # "completed" | "ongoing"

    description = Column(String(5000))
    poster_url = Column(String(500))
    thumb_url = Column(String(500))
    trailer_url = Column(String(500))

    quality = Column(String(50))      
    lang = Column(String(50))         
    time = Column(String(50))       
    year = Column(Integer)
    view = Column(Integer, default=0)

    episode_current = Column(String(50))   
    episode_total = Column(String(50))     

    is_copyright = Column(Boolean, default=False)
    sub_docquyen = Column(Boolean, default=False)
    chieurap = Column(Boolean, default=False)
    notify = Column(String(500))
    showtimes = Column(String(200))

    is_deleted = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_by = Column(String(50))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50))

    # One-to-many
    episodes = relationship("EpisodeModel", back_populates="movie", cascade="all, delete-orphan")
    external_ids = relationship("MovieExternalIdsModel", back_populates="movie", uselist=False, cascade="all, delete-orphan")

    # Many-to-many
    actors = relationship("ActorModel", secondary=movie_actor_association, back_populates="movies")
    directors = relationship("DirectorModel", secondary=movie_director_association, back_populates="movies")
    categories = relationship("CategoryModel", secondary=movie_category_association, back_populates="movies")
    countries = relationship("CountryModel", secondary=movie_country_association, back_populates="movies")

    collection_items = relationship("CollectionItemModel", back_populates="movie", cascade="all, delete-orphan")
    shorts= relationship("ShortModel", back_populates="movie", cascade="all, delete-orphan")
