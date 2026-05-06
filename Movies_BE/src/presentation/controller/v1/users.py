from fastapi import APIRouter, Depends

from src.application.interfaces.services.users_service_interface import ICreateUserService, ILoginUser
from src.presentation.controller.dependencies import ICreateUserDependency, ILoginUserDependency
from src.presentation.dtos.user_dto import LoginDTO, UserCreateDTO


router = APIRouter()

@router.get("/")
async def get_user():
    return {
        "status": "success",
        "data": "Gọi được user"
    }


@router.post("/signup")
async def create_user(
    user_data: UserCreateDTO,
    create_user_service: ICreateUserService = Depends(ICreateUserDependency)
):
    print("Vào được đây")
    result = await create_user_service.create_user(user_data)
    if result is None:
        return {
            "status": "error",
            "data": "Email and password are required"
        }
    return {
        "status": "success",
        "data": result
    }

@router.post("/login")
async def login_user(
    login_dto: LoginDTO,
    login_user_service: ILoginUser = Depends(ILoginUserDependency)
):
    result = await login_user_service.login(login_dto)
    if result is None:
        return {
            "status": "error",
            "data": "Login failed"
        }
    return {
        "status": "success",
        "data": result
    }