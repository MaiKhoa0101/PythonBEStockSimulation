from sqlalchemy import Column, DateTime, Integer,String, Float
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class UserModel(Base):
    __tablename__ = "user"

    id = Column(String(50), primary_key=True, server_default=func.uuid())
    name = Column(String(50))
    email = Column(String(50))
    password = Column(String(100))
    
    # Audit Fields
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50))

    # Mối quan hệ: 1 User có nhiều danh sách yêu thích
    # Truy cập dữ liệu liên kết "không cần dùng JOIN"
    favourite_lists = relationship("FavouriteListModel", back_populates="user")