from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class UserModel(Base):
    __tablename__ = "user"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    avatar = Column(String(100),default=None)
    full_name = Column(String(100))
    username = Column(String(50))
    email = Column(String(50))
    phone_number = Column(String(15))
    password = Column(String(100))
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    premium_until = Column(DateTime, nullable=True)
    role = Column(String(50),default="user")
    
    # Audit Fields
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )    
    created_by = Column(String(50))
    updated_by = Column(String(50))


    collections = relationship("CollectionModel", back_populates="user")
    transactions = relationship("TransactionModel", back_populates="user")
    shorts = relationship("ShortModel", back_populates= "user")