from fastapi import APIRouter, Depends

from src.application.interfaces.services.users_service_interface import ICreateUserService
from src.presentation.controller.dependencies import ICreateUserDependency
from src.presentation.dtos.user_dto import UserCreateDTO


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
async def login_user():
    return {
        "status": "success",
        "data": "User logged in successfully"
    }