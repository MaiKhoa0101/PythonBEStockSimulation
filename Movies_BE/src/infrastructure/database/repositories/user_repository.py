
from requests import Session

from src.domain.entities.users.user import User
from src.application.interfaces.repositories.users_repository_interface import IUserRepository
from src.infrastructure.database.models.movies.user_model import UserModel


class UserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: User) -> User:
        new_user = UserModel(
            id=user.id,
            email=user.email,
            password=user.password,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return User(
            id=new_user.id,
            email=new_user.email,
            password=new_user.password,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified
        )