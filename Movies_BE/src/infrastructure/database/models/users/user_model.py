from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class UsersModel(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True)
    email = Column(String(100), unique=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50))

    favourited_movies = relationship("FavouriteListModel", back_populates="user")