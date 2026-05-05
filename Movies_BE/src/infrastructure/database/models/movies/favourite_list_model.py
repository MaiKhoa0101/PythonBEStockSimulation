from sqlalchemy import Column,DateTime, ForeignKey,String, Float
from src.infrastructure.database.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class FavouriteListModel(Base):
    __tablename__ = "favourite_list"

    id = Column("id",String(50), primary_key= True, server_default= func.uuid())
    name = Column("name_list",String(100))
    user_id= Column(String(50),ForeignKey ("user.id"))
    movie_id = Column(String(50),ForeignKey ("movie.id"))
    
    # Audit Fields
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(50))

    user = relationship("UserModel", back_populates="favourite_lists")
    movie = relationship("MovieModel", back_populates="favourited_by")  