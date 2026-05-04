from fastapi import APIRouter, Depends, Path

from src.presentation.dtos.movie_dto import MovieCreateDTO, MoviePatchDTO, MovieUpdateDTO
from src.domain.entities.movie import Movie
from src.application.interfaces.services.movies_service_interface import IGetListMoviesService, IGetMoviesDetailById, IGetMoviesDetailByName, ICreateMovie, IPatchMovie, IUpdateEntireMovie
from src.presentation.controller.dependencies import ICreateMovieDependency, IDeleteMovieDependency, IGetListMoviesServiceDependency, IGetMoviesDetailByIdDependency, IGetMoviesDetailByNameDependency, IPatchMovieDependency, IUpdateEntireMovieDependency

router = APIRouter()

@router.get("/")
async def api_get_movie_list(
    getListMovieService: IGetListMoviesService = Depends(IGetListMoviesServiceDependency)
):
    # Gọi hàm execute của Query
    result = await getListMovieService.fetch_movies_list()
    if result:
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Lấy danh sách không thành công"
        }

@router.get("/name/{name}")
async def api_get_movie_detail_by_name(
    name: str,
    getMovieByNameService: IGetMoviesDetailByName = Depends(IGetMoviesDetailByNameDependency)
):
    # Gọi hàm execute của Query
    result = await getMovieByNameService.fetch_movie_detail_by_name(name)
    if result:
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Tìm không thành công"
        }


@router.get("/id/{id}")
async def api_get_movie_detail_by_id(
    id: str,
    getMovieByIdService: IGetMoviesDetailById = Depends(IGetMoviesDetailByIdDependency)
):
    # Gọi hàm execute của Query
    result = await getMovieByIdService.fetch_movie_detail_by_id(id)
    if result:
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Tìm không thành công"
        }


@router.post("/create")
async def api_create_movie(
    movie_data: MovieCreateDTO,
    createMovieService: ICreateMovie = Depends(ICreateMovieDependency)
):
    result = await createMovieService.create_movie(
        movie_data
    )
    print(f"result create: {result}")
    if result:
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Update không thành công"
        }

@router.post("/favourite_list/{name}")
async def api_post_movie_into_favourite_list(
    name:str,
):
    return{
        "status":"Success",
        "data":"Thành công"
    }

@router.put("/update/{id}")
async def api_update_movie(
    id:str = Path(...),
    updateMovieDTO: MovieUpdateDTO = ...,
    updateEntireMovieService : IUpdateEntireMovie = Depends(IUpdateEntireMovieDependency)
):
    result = await updateEntireMovieService.update_entire_movie(
        id,
        updateMovieDTO
    )
    if result:
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Update không thành công"
        }

@router.patch("/patch-movie/{id}")
async def api_patch_movie(
    id:str = Path(...),
    update_batch_movie: MoviePatchDTO = ...,
    patchMovieService: IPatchMovie= Depends(IPatchMovieDependency)
):
    result = await patchMovieService.patch_movie(id,update_batch_movie)
    if result:
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Update không thành công"
        }


@router.delete("/delete-by-id/{id}")
async def api_delete_movie(
    id:str =Path(...),
    deleteMovieByIdService= Depends(IDeleteMovieDependency)
):
    result = await deleteMovieByIdService.delete_movie_by_id(id)
    
    if result:
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Xóa không thành công"
        }