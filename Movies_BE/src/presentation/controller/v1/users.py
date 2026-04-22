from fastapi import APIRouter, Depends


router = APIRouter()

@router.get("/")
async def get_user():
    return {
        "status": "success",
        "data": "Gọi được user"
    }