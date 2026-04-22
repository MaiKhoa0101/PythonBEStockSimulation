from fastapi import APIRouter, Depends

from src.application.interfaces.services.movies_data_interface import IMoviesService
from src.presentation.controller.dependencies import IMoviesServiceDependency

router = APIRouter(prefix="/movies", tags=["Movies Data"])

@router.get("/")
async def api_get_hose_index(
    listMovieService: IMoviesService = Depends(IMoviesServiceDependency)
):
    # Gọi hàm execute của Query
    result = await listMovieService.fetch_movies_list()
    return {
        "status": "success",
        "data": result
    }