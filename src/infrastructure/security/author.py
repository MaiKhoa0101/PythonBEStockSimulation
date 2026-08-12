from fastapi import Depends, HTTPException, status
from src.infrastructure.database.session import get_db_mysql
from src.infrastructure.database.models.users.user_model import UserModel
from src.infrastructure.security.security import get_current_user_id
from sqlalchemy.orm import Session, joinedload

class RoleChecker:
    def __init__(
        self, 
        allowed_roles: list[str]
    ):
        self.allowed_roles = allowed_roles

    async def check(
        self, 
        current_user_id: str = Depends(get_current_user_id),
        db: Session = Depends(get_db_mysql)
    ):
        print(f"user id lay duoc cho author la: {current_user_id}")
        user = db.query(UserModel).filter(UserModel.id == current_user_id).first()

        print("check role user: ",user)        
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập tính năng này!"
            )
            
        return current_user_id 