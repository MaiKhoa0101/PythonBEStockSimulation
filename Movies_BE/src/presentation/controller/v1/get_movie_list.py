from fastapi import APIRouter, Depends

from src.application.interfaces.services.movies_data_interface import IMoviesService
from src.presentation.controller.dependencies import IMoviesServiceDependency

router = APIRouter()

@router.get("/movies")
async def api_get_movie_list(
    listMovieService: IMoviesService = Depends(IMoviesServiceDependency)
):
    # Gọi hàm execute của Query
    result = await listMovieService.fetch_movies_list()
    return {
        "status": "success",
        "data": result
    }

@router.get("/{name}")
async def api_get_movie_detail_by_name(
    name: str,
    listMovieService: IMoviesService = Depends(IMoviesServiceDependency)
):
    # Gọi hàm execute của Query
    result = await listMovieService.fetch_movie_detail_by_name(name)
    return {
        "status": "success",
        "data": result
    }