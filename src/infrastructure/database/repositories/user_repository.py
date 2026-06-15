
from dataclasses import asdict

from sqlalchemy.orm import Session, joinedload

from src.infrastructure.database.utils.mapping import model_to_entity
from src.infrastructure.database.models.users.user_model import UserModel
from src.domain.entities.users.user import User
from src.application.interfaces.repositories.users_repository_interface import IUserRepository
from sqlalchemy import inspect as sa_inspect


class UserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    async def create_user(self, user: User) -> User:
        new_user = UserModel(
            username= user.username,
            email=user.email,
            password=user.password,
            full_name=user.full_name,
            phone_number=user.phone_number,
            is_active=user.is_active,
            is_verified=user.is_verified
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        user.id = new_user.id
        user.created_at = new_user.created_at
        user.updated_at = new_user.updated_at
        return user 
    
    async def get_user_by_id(self, user_id: str) -> User:
        print (f"Tim user voi id: {user_id}")
        db_user =  self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            print("tim ko co user")
            return None
        user =model_to_entity(
            db_user,
            User
        )
        return user
        
    
    async def get_user_by_email(self, email: str) -> User:
        user =  self.db.query(UserModel).filter(UserModel.email == email).first()
        if user:
            return User(
                id=user.id,
                username=user.username,
                email=user.email,
                phone_number=user.phone_number,
                password=user.password,
                avatar= user.avatar,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
                role= user.role
            )
        return None
    
    async def update_user(self, user_id: str, user_data: User) -> User:
        print("vao duoc repo")
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return None
        valid_columns = {col.key for col in sa_inspect(UserModel).mapper.column_attrs}
        exclude = {"id", "created_at", "updated_at"}
        for k, v in asdict(user_data).items():
            if k in valid_columns and k not in exclude and v is not None:
                setattr(db_user, k, v)

        
        self.db.commit()
        self.db.refresh(db_user)
        
        user_data = model_to_entity(
            db_user,
            User
        )
        return user_data
    
    async def delete_user(self, user_id: str) -> None:
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if user:
            self.db.delete(user)
            self.db.commit()