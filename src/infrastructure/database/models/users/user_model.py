from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class UserModel(Base):
    __tablename__ = "user"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(100))
    username = Column(String(50))
    email = Column(String(50))
    phone_number = Column(String(15))
    password = Column(String(100))
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # Audit Fields
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50))


    collections = relationship("CollectionModel", back_populates="user")