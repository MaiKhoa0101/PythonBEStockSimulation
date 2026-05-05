from fastapi import APIRouter, Depends


router = APIRouter()

@router.get("/")
async def get_user():
    return {
        "status": "success",
        "data": "Gọi được user"
    }
@router.post("/signup")
async def create_user():
    return {
        "status": "success",
        "data": "User created successfully"
    }

@router.post("/login")
async def login_user():
    return {
        "status": "success",
        "data": "User logged in successfully"
    }