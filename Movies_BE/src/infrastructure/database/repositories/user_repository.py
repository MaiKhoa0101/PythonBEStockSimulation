
from requests import Session

from src.infrastructure.database.models.users.user_model import UserModel
from src.domain.entities.users.user import User
from src.application.interfaces.repositories.users_repository_interface import IUserRepository


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
    
    def get_user_by_id(self, user_id: str) -> User:
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if user:
            return User(
                id=user.id,
                username=user.username,
                email=user.email,
                phone_number=user.phone_number,
                password=user.password,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        return None
    
    def get_user_by_email(self, email: str) -> User:
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if user:
            return User(
                id=user.id,
                email=user.email,
                password=user.password,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified
            )
        return None
    
    def update_user(self, user_id: str, user_data: User) -> User:
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return None
        
        user.email = user_data.email
        user.password = user_data.password
        user.full_name = user_data.full_name
        user.is_active = user_data.is_active
        user.is_verified = user_data.is_verified
        
        self.db.commit()
        self.db.refresh(user)
        
        return User(
            id=user.id,
            email=user.email,
            password=user.password,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified
        )
    
    def delete_user(self, user_id: str) -> None:
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if user:
            self.db.delete(user)
            self.db.commit()