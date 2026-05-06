import uuid

from sqlalchemy import Column,DateTime, ForeignKey,String, Float
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class CollectionModel(Base):
    __tablename__ = "collections"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("CollectionItemModel", back_populates="collection", cascade="all, delete-orphan")
    user = relationship("UserModel", back_populates="collections")

class CollectionItemModel(Base):
    __tablename__ = "collection_items"
    
    collection_id = Column(String(50), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    movie_id = Column(String(50), ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    collection = relationship("CollectionModel", back_populates="items")
    movie = relationship("MovieModel", back_populates="collection_items")