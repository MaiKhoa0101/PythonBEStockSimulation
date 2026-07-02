from fastapi import APIRouter, Depends

from src.infrastructure.security.security import create_access_token
from src.application.interfaces.services.users_service_interface import ICreateUserService, IGetUserById, ILoginUser
from src.presentation.controller.dependencies import ICreateUserDependency, ILoginUserDependency, IUserGetByIdDependency
from src.presentation.dtos.user_dto import LoginDTO, UserCreateDTO


router = APIRouter()

# @router.get("/{id}")
# async def fetchUserById(
#     get_user_service: IGetUserById = Depends(IUserGetByIdDependency)
# ):
#     result = await create_user_service..fetch_movies_list()

#     return {
#         "status": "success",
#         "data": "Gọi được user"
#     }

@router.get("/")
async def check():
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

@router.get("/get_by_id_for_self/{id}")
async def get_user_by_id_for_self(
    id: str,
    get_user_by_id: IGetUserById = Depends(IUserGetByIdDependency)
):
    result = await get_user_by_id.get_user_by_id_for_self(user_id=id)
    token_data = {
            "id": str(result.id),
            "full_name":str(result.full_name),
            "username":str(result.username),
            "email":str(result.email),
            "phone_number":str(result.phone_number),
            "premium_until":str(result.premium_until),
            "avatar":str(result.avatar),
            "role":str(result.role)
        }
    access_token = create_access_token(data=token_data)

    if result is None:
        return {
            "status": "error",
            "data": "Login failed"
        }
    return {
        "status": "success",
        "data": {
            "token" : access_token,
            "user" :result

        }
    }

@router.get("/get_by_id/{id}")
async def get_user_by_id(
    id: str,
    get_user_by_id: IGetUserById = Depends(IUserGetByIdDependency)
):
    result = await get_user_by_id.get_user_by_id(id)

    if result is None:
        return {
            "status": "error",
            "data": "Login failed"
        }
    return {
        "status": "success",
        "data": result

        
    }