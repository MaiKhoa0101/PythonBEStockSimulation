from sqlalchemy import Column, Integer, String
from sqlalchemy import Column, Integer, String, ForeignKey
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class MovieServer(Base):
    __tablename__ = "movie_servers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(String, ForeignKey("movies.id"))
    server_name = Column(String) # Chứa chữ "#Hà Nội (Vietsub)"

    movie = relationship("Movie", back_populates="servers")
    episodes = relationship("Episode", back_populates="server", cascade="all, delete-orphan")