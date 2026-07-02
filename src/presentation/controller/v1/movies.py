# src/presentation/controller/movie_controller.py
import asyncio
import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, Path, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi_cache import FastAPICache

from src.infrastructure.services.logs.admin_log_service import write_audit_log
from src.application.interfaces.services.movies_service_interface import (
    ICreateMovie,
    IDeleteMovie,
    IGetListMoviesService,
    IGetMoviesDetailById,
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
    IGetVideoUrlServiceDependency,
    IPatchMovieDependency,
    IUpdateEntireMovieDependency,
    IUploadEpisodeServiceDepedency,
)
from src.presentation.dtos.movie_dto import MovieCreateDTO, MoviePatchDTO, MovieUpdateDTO

_TASK_SYNC_MOVIE = "src.infrastructure.celery.elastic_task_movie.sync_movie_to_es"
_TASK_DEL_MOVIE  = "src.infrastructure.celery.elastic_task_movie.delete_movie_from_es"
_TASK_BULK_SYNC  = "src.infrastructure.celery.elastic_task_movie.task_bulk_sync_all_movies_to_es"

router = APIRouter()
require_watchable_role = RoleChecker(["admin", "premium"])
require_admin          = RoleChecker(["admin"])

async def _evict_cache(cache_key: str) -> None:

    await FastAPICache.get_backend().clear(cache_key)


def _warm_cache(cache_key: str, data: dict, expire: int) -> None:

    asyncio.create_task(
        FastAPICache.get_backend().set(cache_key, json.dumps(data), expire=expire)
    )


@router.get("/")
async def api_get_movie_list(
    getListMovieService: IGetListMoviesService = Depends(IGetListMoviesServiceDependency),
):
    result = await getListMovieService.fetch_movies_list()
    if result:
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Lấy danh sách không thành công"}


@router.get("/listhome")
async def api_get_movie_list_home():
    cache_key = "movie:list:home"
    backend   = FastAPICache.get_backend()

    cached = await backend.get(cache_key)
    if cached:
        return {"status": "Success", "data": json.loads(cached)}

    result = fetch_movies_list_home_from_es(page=1, size=20)
    if result:
        serializable_data = jsonable_encoder(result)
        _warm_cache(cache_key, serializable_data, expire=120)   # ← asyncio.create_task bên trong
        return {"status": "Success", "data": serializable_data}

    return {"status": "Failed", "data": "Lấy danh sách không thành công"}


@router.get("/search")
def api_search_movies(q: str):
    if not q or not q.strip():
        return {"status": "Failed", "data": "Vui lòng nhập từ khóa tìm kiếm"}
    result = search_movies(q.strip())
    return {"status": "Success", "data": result}


@router.get("/name/{name}")
async def api_get_movie_detail_by_name(name: str):
    cache_key = f"movie:detail:{name}"
    backend   = FastAPICache.get_backend()

    cached = await backend.get(cache_key)
    if cached:
        return {"status": "Success", "data": json.loads(cached)}

    result = get_movie_by_slug_from_es(name)
    if result:
        serializable_data = jsonable_encoder(result)
        _warm_cache(cache_key, serializable_data, expire=3600)
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
    celery_instance.send_task(_TASK_BULK_SYNC)
    return {"status": "Success", "data": "Đã kích hoạt sync toàn bộ phim"}


# ─────────────────────────────────────────────────────────────────────────────
# WRITE Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/create")
async def api_create_movie(
    movie_data: MovieCreateDTO,
    current_user_id: str = Depends(require_admin.check),
    createMovieService: ICreateMovie = Depends(ICreateMovieDependency),
):
    result = await createMovieService.create_movie(movie_data)
    if result:
        celery_instance.send_task(_TASK_SYNC_MOVIE, args=[result.id])
        write_audit_log(                     
            action="CREATE",
            admin_id=current_user_id,
            movie_id=result.id,
            movie_title=result.name,
            new_values={"name": result.name, "slug": result.slug_name},
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
):
    result = await updateEntireMovieService.update_entire_movie(id, updateMovieDTO)
    if result:
        cache_key = f"movie:detail:{result.slug_name}"
        background_tasks.add_task(_evict_cache, cache_key)

        write_audit_log(                  
            action="UPDATE",
            admin_id=current_user_id,
            movie_id=result.id,
            movie_title=result.name,
            new_values={"name": result.name, "slug": result.slug_name},
        )
        celery_instance.send_task(
            "tasks.sync_movie", 
            args=[result.id, cache_key],
            queue="light_queue"
        )
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Update không thành công"}


@router.patch("/patch-movie/{id}")
async def api_patch_movie(
    background_tasks: BackgroundTasks,
    id: str = Path(...),
    update_batch_movie: MoviePatchDTO = ...,
    current_user_id: str = Depends(require_admin.check),
    patchMovieService: IPatchMovie = Depends(IPatchMovieDependency),
):
    result = await patchMovieService.patch_movie(id, update_batch_movie)
    if result:
        background_tasks.add_task(_evict_cache, f"movie:detail:{result.slug_name}")
        celery_instance.send_task(_TASK_SYNC_MOVIE, args=[id])

        write_audit_log(                    
            action="PATCH",
            admin_id=current_user_id,
            movie_id=result.id,
            movie_title=result.name,
            new_values={"name": result.name, "slug": result.slug_name},
        )
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Update không thành công"}


@router.delete("/delete-by-id/{id}")
async def api_delete_movie(
    background_tasks: BackgroundTasks,
    id: str = Path(...),
    current_user_id: str = Depends(require_admin.check),
    deleteMovieService: IDeleteMovie = Depends(IDeleteMovieDependency),
):
    result = await deleteMovieService.delete_movie_by_id(id)

    write_audit_log(                    
        action="DELETE",
        admin_id=current_user_id,
        movie_id=result.id,
        movie_title=result.name,
        new_values={"name": result.name, "slug": result.slug_name},
    )
    if result:
        background_tasks.add_task(_evict_cache, f"movie:detail:{result.slug_name}")
        celery_instance.send_task(_TASK_DEL_MOVIE, args=[id])
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Xóa không thành công"}


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