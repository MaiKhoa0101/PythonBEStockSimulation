from src.infrastructure.database.models.shorts.short_model import ShortModel
from src.domain.entities.short.short import Short
from src.application.interfaces.repositories.short_repository_interface import IShortRepository
from sqlalchemy.orm import Session, joinedload
from src.infrastructure.database.utils.mapping import entity_to_model, model_to_entity


class ShortRepository(IShortRepository):
    def __init__(self, db: Session): 
        self.db = db

    async def get_shorts(self, id:str = None):
        print("Vào tới repo")
        short:list[Short]=[]
        if id:
            db_short = self.db.query(ShortModel).filter(
                ShortModel.user_id==id,
                ShortModel.is_deleted == False
            ).limit(5)
            if not db_short:
                return None
            short = [
                model_to_entity(i, Short)
                for i in db_short
            ]
        else:
            db_short = self.db.query(ShortModel).filter(
                ShortModel.is_deleted == False
            ).limit(5)
            if not db_short:
                return None
            short = [
                model_to_entity(i, Short)
                for i in db_short
            ]
        return short

    async def get_shorts_by_user_id(self,id:str):
        db_short = self.db.query(ShortModel).filter(
            ShortModel.user_id==id,
            ShortModel.is_deleted == False
        ).all()
        if not db_short:
            return None
        short = [
            model_to_entity(i, Short)
            for i in db_short
        ]
        return short

    async def get_shorts_by_movie_id(self,id:str):
        db_short = self.db.query(ShortModel).filter(
            ShortModel.user_id==id,
            ShortModel.is_deleted == False
        ).all()

        if not db_short:
            return None
        short = [
            model_to_entity(i, Short)
            for i in db_short
        ]        
        return short
    
    async def get_shorts_by_episode_id(self,id:str):
        db_short = self.db.query(ShortModel).filter(
            ShortModel.user_id==id,
            ShortModel.is_deleted == False
        ).all()
        
        if not db_short:
            return None
        
        short = [
            model_to_entity(i, Short)
            for i in db_short
        ]
        return short    
    
    async def get_short_by_self_id(self,id:str):
        db_short = self.db.query(ShortModel).filter(
            ShortModel.user_id==id, 
            ShortModel.is_deleted == False
        ).first()

        if not db_short:
            return None
        short = model_to_entity(db_short, Short)
        return short

    async def create_short(self,short:Short):
        db_short= entity_to_model(short,ShortModel)

        self.db.add(db_short)
        self.db.commit()
        self.db.refresh(db_short)
        
        short.id=db_short.id
        short.created_at=db_short.created_at
        short.updated_at=db_short.updated_at

        return short

    async def delete_short(self,id:str):
        db_short = self.db.query(ShortModel).filter(
            ShortModel.id == id,
            ShortModel.is_deleted == False
        ).first()

        db_short.is_deleted=True

        self.db.commit()
        