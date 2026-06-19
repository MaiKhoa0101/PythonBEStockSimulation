import json
import os
from redis.asyncio import Redis as AsyncRedis
from src.infrastructure.elasticsearch.search import search_movies
from src.infrastructure.celery.elastic_task_movie import sync_movie_to_es, delete_movie_from_es, task_bulk_sync_all_movies_to_es
from fastapi import APIRouter, BackgroundTasks, Depends, File, Path, UploadFile
from fastapi_cache import FastAPICache
from fastapi.encoders import jsonable_encoder
from src.infrastructure.database.redis import get_redis_client
from src.infrastructure.security.author import RoleChecker
from src.infrastructure.security.security import get_current_user_id
from src.presentation.dtos.movie_dto import MovieCreateDTO, MoviePatchDTO, MovieUpdateDTO
from src.domain.entities.movies.movie import Movie
from src.application.interfaces.services.movies_service_interface import IGetListMoviesService, IGetMoviesDetailById, IGetMoviesDetailByName, ICreateMovie, IGetVideoUrlService, IPatchMovie, IUpdateEntireMovie, IUploadEpisode
from src.presentation.controller.dependencies import ICreateMovieDependency, IDeleteMovieDependency, IGetListMoviesServiceDependency, IGetMoviesDetailByIdDependency, IGetMoviesDetailByNameDependency, IGetVideoUrlServiceDependency, IPatchMovieDependency, IUpdateEntireMovieDependency, IUploadEpisodeServiceDepedency
from fastapi_cache.decorator import cache

router = APIRouter()
require_watchable_role = RoleChecker(["admin", "premium"])
require_admin = RoleChecker(["admin"])

@router.get("/")
async def api_get_movie_list(
    getListMovieService: IGetListMoviesService = Depends(IGetListMoviesServiceDependency)
):
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

@router.get("/search")
async def api_search_movies(
    q: str,
):
    if not q or not q.strip():
        return {"status": "Failed", "data": "Vui lòng nhập từ khóa tìm kiếm"}

    result = search_movies(q.strip())
    return {
        "status": "Success",
        "data": result
    }

@router.get("/sync_movie")
async def api_sync_movie():
    task_bulk_sync_all_movies_to_es.delay()

@router.get("/name/{name}")
async def api_get_movie_detail_by_name(
    name: str,
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
        
        await redis_backend.set(
            cache_key, 
            json.dumps(serializable_data), 
            expire=10
        )
        
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
    current_user_id: str = Depends(require_admin.check),
    createMovieService: ICreateMovie = Depends(ICreateMovieDependency)
):
    result = await createMovieService.create_movie(
        movie_data
    )
    print(f"result create: {result}")
    if result:
        sync_movie_to_es.delay(result.id)
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
    current_user_id: str = Depends(require_admin.check),
    updateEntireMovieService : IUpdateEntireMovie = Depends(IUpdateEntireMovieDependency),
):
    result = await updateEntireMovieService.update_entire_movie(
        id,
        updateMovieDTO
    )
    background_tasks.add_task(FastAPICache.clear, namespace="movie")
    if result:
        sync_movie_to_es.delay(id)
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
    current_user_id: str = Depends(require_admin.check),
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
    current_user_id: str = Depends(require_admin.check),
    DeleteMovieService= Depends(IDeleteMovieDependency)
):
    result = await DeleteMovieService.delete_movie_by_id(id)
    
    if result:
        delete_movie_from_es.delay(id)
        return{
            "status":"Success",
            "data":result
        }
    else: 
        return{
            "status":"Failed",
            "data":"Xóa không thành công"
        }


# @router.post("/upload-video/{movie_slug}/{episode_slug}/{episode_id}")
# async def api_upload_episode_video_local(
#     movie_slug: str = Path(...),
#     episode_slug: str = Path(...),
#     episode_id: str = Path(...),
#     file: UploadFile = File(...),
#     upload_service: IUploadEpisode = Depends(IUploadEpisodeServiceDepedency)
# ):
#     result_path = await upload_service.upload_episode_video_into_local_system_path(
#         movie_slug, episode_slug, episode_id, file
#     )
#     return {"status": "Success", "data": result_path}

@router.post("/upload-video-hls/{movie_slug}/{episode_slug}")
async def api_upload_episode_video_hls(
    bg_tasks: BackgroundTasks,
    movie_slug: str = Path(...),
    episode_slug: str = Path(...),
    file: UploadFile = File(...),
    current_user_id: str = Depends(require_admin.check),
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
    current_user_id: str = Depends(require_watchable_role.check),
    get_episode_url_service: IGetVideoUrlService = Depends(IGetVideoUrlServiceDependency),
    redis = Depends(get_redis_client)
):
    result = await get_episode_url_service.get_video_url(id_episode)
    print(f"ket qua lay url la {result}")
    if result and result.get("movie_id"):
        await redis.incr(f"view:{result['movie_id']}")

    return {"status": "Success", "data": result}

