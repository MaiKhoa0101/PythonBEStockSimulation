import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import relationship
from src.infrastructure.database.session import Base
from src.infrastructure.database.models.associations.associations import movie_director_association


class DirectorModel(Base):
    __tablename__ = "director"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True)

    movies = relationship("MovieModel", secondary=movie_director_association, back_populates="directors")

