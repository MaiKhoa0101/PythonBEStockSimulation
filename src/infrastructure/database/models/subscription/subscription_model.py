
from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship
from src.infrastructure.database.session import Base


class SubscriptionPackageModel(Base):
    __tablename__="subscription_packages"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)       
    price = Column(Integer, nullable=False)            
    duration_days = Column(Integer, nullable=False) 
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    transactions = relationship("TransactionModel", back_populates="package")