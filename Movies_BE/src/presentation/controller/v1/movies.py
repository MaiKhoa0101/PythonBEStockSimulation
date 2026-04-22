from fastapi import APIRouter, Depends

from src.application.interfaces.services.movies_data_interface import IGetListMoviesService, IGetMoviesDetailByName
from src.presentation.controller.dependencies import IGetListMoviesServiceDependency, IGetMoviesDetailByNameDependency

router = APIRouter()

@router.get("/")
async def api_get_movie_list(
    getListMovieService: IGetListMoviesService = Depends(IGetListMoviesServiceDependency)
):
    # Gọi hàm execute của Query
    result = await getListMovieService.fetch_movies_list()
    return {
        "status": "success",
        "data": result
    }

@router.get("/{name}")
async def api_get_movie_detail_by_name(
    name: str,
    getMovieByNameService: IGetMoviesDetailByName = Depends(IGetMoviesDetailByNameDependency)
):
    # Gọi hàm execute của Query
    result = await getMovieByNameService.fetch_movie_detail_by_name(name)
    return {
        "status": "success",
        "data": result
    }