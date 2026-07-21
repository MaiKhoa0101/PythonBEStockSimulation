import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    amount = Column(Integer, nullable=False)
    status = Column(String(50), default="PENDING")
    payment_method = Column(String(20))

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user_id = Column(String(50), ForeignKey("user.id"), nullable=False)
    package_id = Column(String(50), ForeignKey("subscription_packages.id"), nullable=False)

    user = relationship("UserModel", back_populates="transactions")
    package = relationship("SubscriptionPackageModel", back_populates="transactions")
    