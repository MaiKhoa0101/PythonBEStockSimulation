# src/presentation/controller/movie_controller.py
from datetime import datetime, timezone
import json
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Path, Query, UploadFile
from fastapi.encoders import jsonable_encoder


from src.application.interfaces.services.similar_movies_interface import ISimilarMoviesService
from src.infrastructure.cache.movie_cache import cache_delete, cache_get_json, cache_set_json, invalidate_movie_list_home_cache, movie_detail_key, movie_list_home_key
from src.infrastructure.services.logs.admin_log_service import write_audit_log
from src.application.interfaces.services.movies_service_interface import (
    ICreateMovie,
    IDeleteMovie,
    IGetListMoviesService,
    IGetMoviesDetailById,
    IGetMoviesDetailByName,
    IGetVideoUrlService,
    IPatchMovie,
    IUpdateEntireMovie,
    IUploadEpisode,
)
from src.infrastructure.celery.celery_app import celery_instance 
from src.infrastructure.database.redis import get_redis_client
from src.infrastructure.elasticsearch.fetch_movie import (
    fetch_movies_list_home_from_es,
    get_movie_by_slug_from_es,
)
from src.infrastructure.elasticsearch.search import search_movies
from src.infrastructure.security.author import RoleChecker
from src.presentation.controller.dependencies import (
    ICreateMovieDependency,
    IDeleteMovieDependency,
    IGetListMoviesServiceDependency,
    IGetMoviesDetailByIdDependency,
    IGetMoviesDetailByNameDependency,
    IGetVideoUrlServiceDependency,
    IPatchMovieDependency,
    ISimilarMoviesDependency,
    IUpdateEntireMovieDependency,
    IUploadEpisodeServiceDepedency,
)
from src.presentation.dtos.movie_dto import MovieCreateDTO, MoviePatchDTO, MovieUpdateDTO

_TASK_SYNC_MOVIE = "tasks.sync_movie_to_es"
_TASK_DEL_MOVIE  = "tasks.delete_movie_from_es"
_TASK_SYNC_BULK  = "tasks.bulk_sync_all_movies_to_es"
router = APIRouter()
require_watchable_role = RoleChecker(["admin", "premium"])
require_watchable_free_role = RoleChecker(["admin", "premium","user"])
require_admin          = RoleChecker(["admin"])
logger = logging.getLogger(__name__)

@router.get("/")
async def api_get_movie_list(
    page: int = 1,
    size: int = 20,
    q: Optional[str] = Query(None, description="Từ khóa tìm kiếm phim"),
    category_id: Optional[str] = Query(None, description="Lọc theo id thể loại"),
    country_slug: Optional[str] = Query(None, description="Lọc theo slug quốc gia"),
    status: Optional[str] = Query(None, description="ongoing | completed"),
    is_series: Optional[bool] = Query(None, description="true = phim bộ, false = phim lẻ"),
    quality: Optional[str] = Query(None, description="HD | FHD | CAM..."),
    year: Optional[int] = Query(None, description="Năm phát hành"),
    getListMovieService: IGetListMoviesService = Depends(IGetListMoviesServiceDependency),
):
    result = await getListMovieService.fetch_movies_list(
        page=page,
        size=size,
        q=q,
        category_id=category_id,
        country_slug=country_slug,
        status=status,
        is_series=is_series,
        quality=quality,
        year=year,
    )
    if result:
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Lấy danh sách không thành công"}

@router.get("/listhome")
async def api_get_movie_list_home(
    page: int = 1,
    size: int = 20,
    getMovieListHomeService: IGetListMoviesService = Depends(IGetListMoviesServiceDependency),
    redis=Depends(get_redis_client)
):
    cache_key = f"{movie_list_home_key()}:page:{page}"

    cached = await cache_get_json(redis, cache_key)
    if cached is not None:
        return {"status": "Success", "data": cached}

    try:
        result = fetch_movies_list_home_from_es(page, size)
    except Exception as e:
        logger.error(f"ES lỗi khi lấy listhome, fallback về DB: {e}")
        result = None

    if not result:
        db_result = await getMovieListHomeService.fetch_movies_list(page=page, size=size)
        result = db_result["results"]  

    if result:
        serializable_data = jsonable_encoder(result)
        await cache_set_json(redis, cache_key, serializable_data, expire=120)
        return {"status": "Success", "data": serializable_data}

    return {"status": "Failed", "data": "Lấy danh sách không thành công"}

@router.get("/search")
async def api_search_movies(
    q: str,
    getListMovieService: IGetListMoviesService = Depends(IGetListMoviesServiceDependency),
):
    if not q or not q.strip():
        return {"status": "Failed", "data": "Vui lòng nhập từ khóa tìm kiếm"}

    try:
        result = await search_movies(q.strip())
    except Exception as e:
        logger.error(f"ES lỗi khi search '{q}': {e}")
        result = None

    if not result:
        db_result = await getListMovieService.fetch_movies_list(page=1, size=20, q=q.strip())
        result = {"results": db_result["results"]}

    return {"status": "Success", "data": result}

@router.get("/name/{name}")
async def api_get_movie_detail_by_name(
    name: str,
    getMoviesDetailByNameService: IGetMoviesDetailByName = Depends(IGetMoviesDetailByNameDependency),
    redis=Depends(get_redis_client)
):
    cache_key = movie_detail_key(name)

    cached = await cache_get_json(redis, cache_key)
    if cached is not None:
        return {"status": "Success", "data": cached}

    try:
        result = await get_movie_by_slug_from_es(name)
    except Exception as e:
        logger.error(f"ES lỗi khi lấy movie detail theo slug '{name}': {e}")
        result = None

    if not result:

        result = await getMoviesDetailByNameService.fetch_movie_detail_by_name(name)

    if result:
        serializable_data = jsonable_encoder(result)
        await cache_set_json(redis, cache_key, serializable_data, expire=60)
        return {"status": "Success", "data": serializable_data}

    return {"status": "Failed", "data": "Tìm không thành công"}

@router.get("/id/{id}")
async def api_get_movie_detail_by_id(
    id: str,
    getMovieByIdService: IGetMoviesDetailById = Depends(IGetMoviesDetailByIdDependency),
):
    result = await getMovieByIdService.fetch_movie_detail_by_id(id)
    if result:
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Tìm không thành công"}

@router.get("/sync_movie")
async def api_sync_movie():
    celery_instance.send_task(_TASK_SYNC_BULK, queue="light_queue")
    return {"status": "Success", "data": "Đã kích hoạt sync toàn bộ phim"}

@router.get("/similar/{movie_id}")
async def api_get_similar_movies(
    movie_id: str = Path(...),
    limit: int = 5,
    similarMoviesService: ISimilarMoviesService = Depends(ISimilarMoviesDependency),
):
    result = await similarMoviesService.get_similar_movies(movie_id, limit)
    return {"status": "Success", "data": result}
# ─────────────────────────────────────────────────────────────────────────────
# WRITE Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/create")
async def api_create_movie(
    movie_data: MovieCreateDTO,
    current_user_id: str = Depends(require_admin.check),
    createMovieService: ICreateMovie = Depends(ICreateMovieDependency),
    redis=Depends(get_redis_client),
):
    result = await createMovieService.create_movie(movie_data)
    if result:
        celery_instance.send_task(_TASK_SYNC_MOVIE, args=[result.id], queue="light_queue")
        await invalidate_movie_list_home_cache(redis)
        write_audit_log(
            action="CREATE",
            admin_id=current_user_id,
            movie_id=result.id,
            movie_title=result.name,
            new_values=movie_data.model_dump()
        )
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Tạo không thành công"}


@router.put("/update/{id}")
async def api_update_movie(
    background_tasks: BackgroundTasks,
    id: str = Path(...),
    updateMovieDTO: MovieUpdateDTO = ...,
    current_user_id: str = Depends(require_admin.check),
    updateEntireMovieService: IUpdateEntireMovie = Depends(IUpdateEntireMovieDependency),
    redis=Depends(get_redis_client),
):
    result = await updateEntireMovieService.update_entire_movie(id, updateMovieDTO)
    if result:
        background_tasks.add_task(cache_delete, redis, movie_detail_key(result.slug_name))
        background_tasks.add_task(invalidate_movie_list_home_cache, redis)  

        write_audit_log(
            action="UPDATE",
            admin_id=current_user_id,
            movie_id=result.id,
            movie_title=result.name,
            new_values=updateMovieDTO.model_dump()
        )
        celery_instance.send_task(_TASK_SYNC_MOVIE, args=[result.id], queue="light_queue")
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Update không thành công"}

@router.patch("/patch-movie/{id}")
async def api_patch_movie(
    background_tasks: BackgroundTasks,
    id: str = Path(...),
    update_batch_movie: MoviePatchDTO = ...,
    current_user_id: str = Depends(require_admin.check),
    patchMovieService: IPatchMovie = Depends(IPatchMovieDependency),
    redis=Depends(get_redis_client),
):
    result = await patchMovieService.patch_movie(id, update_batch_movie)
    if result:
        background_tasks.add_task(cache_delete, redis, movie_detail_key(result.slug_name))
        background_tasks.add_task(invalidate_movie_list_home_cache, redis)

        write_audit_log(
            action="PATCH",
            admin_id=current_user_id,
            movie_id=result.id,
            movie_title=result.name,
            new_values=update_batch_movie.model_dump()
        )
        celery_instance.send_task(_TASK_SYNC_MOVIE, args=[result.id], queue="light_queue")
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Update không thành công"}

@router.delete("/delete-by-id/{id}")
async def api_delete_movie(
    background_tasks: BackgroundTasks,
    id: str = Path(...),
    current_user_id: str = Depends(require_admin.check),
    deleteMovieService: IDeleteMovie = Depends(IDeleteMovieDependency),
    redis=Depends(get_redis_client),
):
    result = await deleteMovieService.delete_movie_by_id(id)

    if result:
        write_audit_log(
            action="DELETE",
            admin_id=current_user_id,
            movie_id=result.id,
            movie_title=result.name,
            new_values={}
        )
        background_tasks.add_task(cache_delete, redis, movie_detail_key(result.slug_name))
        background_tasks.add_task(cache_delete, redis, f"movie:{id}:similar") 
        background_tasks.add_task(invalidate_movie_list_home_cache, redis)   
        celery_instance.send_task(_TASK_DEL_MOVIE, args=[id], queue="light_queue")
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Xóa không thành công"}


@router.post("/log-view/{movie_id}")
async def log_movie_view(
    movie_id: str,
    episode_id: Optional[str] = None,
    duration_watched: int = 0,
    user_id: str = Depends(require_watchable_free_role.check),
    redis_client = Depends(get_redis_client) 
):
    event_data = {
        "user_id": user_id,
        "movie_id": movie_id,
        "episode_id": episode_id,
        "duration_watched": duration_watched,
        "timestamp":  datetime.now(timezone.utc)
    }
    
    redis_client.rpush("buffer:movie_views", json.dumps(event_data))
    
    return {"status": "success", "message": "View logged to buffer"}
# ─────────────────────────────────────────────────────────────────────────────
# Video & Views Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/upload-video-hls/{movie_slug}/{episode_slug}")
async def api_upload_episode_video_hls(
    bg_tasks: BackgroundTasks,
    movie_slug: str = Path(...),
    episode_slug: str = Path(...),
    file: UploadFile = File(...),
    current_user_id: str = Depends(require_admin.check),
    upload_service: IUploadEpisode = Depends(IUploadEpisodeServiceDepedency),
):
    result_path = await upload_service.upload_episode_video_hls(
        first_folder=movie_slug,
        episode_slug=episode_slug,
        file=file,
        bg_tasks=bg_tasks,
    )
    return {"status": "Success", "data": result_path}


@router.get("/episode/{id_episode}")
async def api_get_episode_url(
    id_episode: str = Path(...),
    current_user_id: str = Depends(require_watchable_role.check),
    get_episode_url_service: IGetVideoUrlService = Depends(IGetVideoUrlServiceDependency),
    redis=Depends(get_redis_client),
):
    result = await get_episode_url_service.get_video_url(id_episode)
    if result and result.get("movie_id"):
        await redis.incr(f"view:{result['movie_id']}")
    return {"status": "Success", "data": result}