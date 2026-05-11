import uuid

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from src.infrastructure.database.session import Base


class MovieExternalIdsModel(Base):
    __tablename__ = "movie_external_ids"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_movie = Column(String(50), ForeignKey("movie.id"), unique=True, nullable=False)

    # TMDB
    tmdb_type = Column(String(50))
    tmdb_id = Column(String(50))
    tmdb_season = Column(Integer)
    tmdb_vote_average = Column(Float)
    tmdb_vote_count = Column(Integer)

    # IMDB
    imdb_id = Column(String(50))

    movie = relationship("MovieModel", back_populates="external_ids")

