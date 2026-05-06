

from src.infrastructure.security.security import create_access_token, verify_password
from src.presentation.dtos.user_dto import LoginDTO, ResponseLoginDTO
from src.application.interfaces.repositories.users_repository_interface import IUserRepository
from src.application.interfaces.services.users_service_interface import ILoginUser


class LoginUser(ILoginUser):
    def __init__(
        self,
        user_repository: IUserRepository
    ):
        self.user_repository= user_repository

    async def login(self, login_data: LoginDTO):

        if not (login_data.email and login_data.password):
            return None
        
        result = self.user_repository.get_user_by_email(
            login_data.email
        )

        if not result:
            return None
        
        is_password_correct = verify_password(login_data.password, result.password)

        if not is_password_correct:
            return None
        
        token_data = {"user_id": str(result.id)}
        access_token = create_access_token(data=token_data)
        response = ResponseLoginDTO(
            token = access_token
        )

        return response