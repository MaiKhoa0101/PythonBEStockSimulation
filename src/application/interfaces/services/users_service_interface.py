from typing import Protocol

from src.presentation.dtos.user_dto import LoginDTO, ResponseLoginDTO, UserCreateDTO, UserResponseDTO, UserUpdateDTO


class ICreateUserService(Protocol):
    async def create_user(user_data: UserCreateDTO) -> UserResponseDTO:
        ...

class IGetUserById(Protocol):
    async def get_user_by_id(user_id: str) -> UserResponseDTO:
        ...

class IGetUserByEmail(Protocol):
    async def get_user_by_email(email: str) -> UserResponseDTO:
        ...

class IUpdateUser(Protocol):
    async def update_user(user_id: str, user_data: UserUpdateDTO) -> UserResponseDTO:
        ...

class IDeleteUser(Protocol):
    async def delete_user(user_id: str) -> None:
        ...

class ILoginUser(Protocol):
    async def login(login_data: LoginDTO) -> ResponseLoginDTO:
        ...