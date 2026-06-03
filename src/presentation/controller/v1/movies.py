import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, Path, UploadFile
from fastapi_cache import FastAPICache
from fastapi.encoders import jsonable_encoder
from src.infrastructure.security.security import get_current_user_id
from src.presentation.dtos.movie_dto import MovieCreateDTO, MoviePatchDTO, MovieUpdateDTO
from src.domain.entities.movies.movie import Movie
from src.application.interfaces.services.movies_service_interface import IGetListMoviesService, IGetMoviesDetailById, IGetMoviesDetailByName, ICreateMovie, IGetVideoUrlService, IPatchMovie, IUpdateEntireMovie, IUploadEpisode
from src.presentation.controller.dependencies import ICreateMovieDependency, IDeleteMovieDependency, IGetListMoviesServiceDependency, IGetMoviesDetailByIdDependency, IGetMoviesDetailByNameDependency, IGetVideoUrlServiceDependency, IPatchMovieDependency, IUpdateEntireMovieDependency, IUploadEpisodeServiceDepedency
from fastapi_cache.decorator import cache

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
    current_user_id: str = None,
    getMovieByNameService: IGetMoviesDetailByName = Depends(IGetMoviesDetailByNameDependency)
):
    redis_backend = FastAPICache.get_backend()
    cache_key = f"movie:detail:{name}" 

    cache_movie = await redis_backend.get(cache_key)
    result = None
    if cache_movie:
        result = json.loads(cache_movie)
        print(f"Lấy từ cache với data {result}")
    else:    
        result = await getMovieByNameService.fetch_movie_detail_by_name(name)
        print(f"Lấy từ service với data {result}")
    
    if result: 
        serializable_data = jsonable_encoder(result)
        
        await redis_backend.set(cache_key, json.dumps(serializable_data), expire=30)
        
        return {
            "status": "Success",
            "data": serializable_data 
        }
    else: 
        return {
            "status": "Failed",
            "data": "Tìm không thành công"
        }
    

@router.get("/id/{id}")
async def api_get_movie_detail_by_id(
    id: str,
    getMovieByIdService: IGetMoviesDetailById = Depends(IGetMoviesDetailByIdDependency)
):
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


@router.put("/update/{id}")
async def api_update_movie(
    background_tasks: BackgroundTasks,
    id:str = Path(...),
    updateMovieDTO: MovieUpdateDTO = ...,
    updateEntireMovieService : IUpdateEntireMovie = Depends(IUpdateEntireMovieDependency),
):
    result = await updateEntireMovieService.update_entire_movie(
        id,
        updateMovieDTO
    )
    background_tasks.add_task(FastAPICache.clear, namespace="movie")
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
    DeleteMovieService= Depends(IDeleteMovieDependency)
):
    result = await DeleteMovieService.delete_movie_by_id(id)
    
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
@router.post("/upload-video/{movie_slug}/{episode_slug}/{episode_id}")
async def api_upload_episode_video_local(
    movie_slug: str = Path(...),
    episode_slug: str = Path(...),
    episode_id: str = Path(...),
    file: UploadFile = File(...),
    upload_service: IUploadEpisode = Depends(IUploadEpisodeServiceDepedency)
):
    result_path = await upload_service.upload_episode_video_into_local_system_path(
        movie_slug, episode_slug, episode_id, file
    )
    return {"status": "Success", "data": result_path}


@router.post("/upload-video-hls/{movie_slug}/{episode_slug}")
async def api_upload_episode_video_hls(
    bg_tasks: BackgroundTasks,
    movie_slug: str = Path(...),
    episode_slug: str = Path(...),
    file: UploadFile = File(...),
    upload_service: IUploadEpisode = Depends(IUploadEpisodeServiceDepedency)
):
    result_path = await upload_service.upload_episode_video_hls(
        first_folder= movie_slug, 
        episode_slug= episode_slug, 
        file=file, 
        bg_tasks=bg_tasks
    )
    print ("Kết quả đường dẫn sau khi upload episode: "+result_path)
    return {"status": "Success", "data": result_path}


@router.get("/episode/{id_episode}")
async def api_get_episode_url(
    id_episode:str= Path(...),
    current_user_id: str = Depends(get_current_user_id),
    get_episode_url_service: IGetVideoUrlService = Depends(IGetVideoUrlServiceDependency)
):
    print("vao toi day")
    result = await get_episode_url_service.get_video_url(id_episode)
    print("ket qua lay link la: ",result)
    return {
        "status": "Success", 
        "data": result
    }
