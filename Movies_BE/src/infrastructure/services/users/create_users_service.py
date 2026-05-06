
from src.infrastructure.security.security import get_password_hash
from src.application.interfaces.repositories.users_repository_interface import IUserRepository
from src.domain.entities.users.user import User
from src.presentation.dtos.user_dto import UserCreateDTO, UserResponseDTO, UserUpdateDTO
from src.application.interfaces.services.users_service_interface import  ICreateUserService


class CreateUserService(ICreateUserService):

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository


    async def create_user(self, user_data: UserCreateDTO) -> UserResponseDTO:
        #ánh xạ từ DTO sang Entity, gọi repository để lưu vào database, 
        #sau đó ánh xạ lại từ Entity sang DTO để trả về

        if not user_data.email or not user_data.password:
            return None
        hashed_password = get_password_hash(user_data.password)
        user_entity = User(
            id="",  
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            password=hashed_password
        )

        result: User = await self.user_repository.create_user(user_entity)

        if not result:
            return None

        response = UserResponseDTO(
            id= result.id,
            username= result.username,
            full_name= result.full_name,
            email= result.email,
            phone_number= result.phone_number,
            created_at= result.created_at,
            updated_at= result.updated_at
        )
        print(f"Service trả về {response}")
        return response