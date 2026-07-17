# src/presentation/controller/movie_controller.py
from fastapi import APIRouter, BackgroundTasks, Depends, File, Path, UploadFile
from fastapi.encoders import jsonable_encoder


from src.infrastructure.cache.movie_cache import cache_delete, cache_get_json, cache_set_json, movie_detail_key, movie_list_home_key
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

_TASK_SYNC_MOVIE = "tasks.sync_movie_to_es"
_TASK_DEL_MOVIE  = "tasks.delete_movie_from_es"
_TASK_SYNC_BULK  = "tasks.bulk_sync_all_movies_to_es"
router = APIRouter()
require_watchable_role = RoleChecker(["admin", "premium"])
require_admin          = RoleChecker(["admin"])

@router.get("/")
async def api_get_movie_list(
    getListMovieService: IGetListMoviesService = Depends(IGetListMoviesServiceDependency),
):
    result = await getListMovieService.fetch_movies_list()
    if result:
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Lấy danh sách không thành công"}


@router.get("/listhome")
async def api_get_movie_list_home(redis=Depends(get_redis_client)):
    cache_key = movie_list_home_key()

    cached = await cache_get_json(redis, cache_key)
    if cached is not None:
        return {"status": "Success", "data": cached}

    result = fetch_movies_list_home_from_es(page=1, size=20)
    if result:
        serializable_data = jsonable_encoder(result)
        await cache_set_json(redis, cache_key, serializable_data, expire=120)
        return {"status": "Success", "data": serializable_data}

    return {"status": "Failed", "data": "Lấy danh sách không thành công"}


@router.get("/search")
def api_search_movies(q: str):
    if not q or not q.strip():
        return {"status": "Failed", "data": "Vui lòng nhập từ khóa tìm kiếm"}
    result = search_movies(q.strip())
    return {"status": "Success", "data": result}


@router.get("/name/{name}")
async def api_get_movie_detail_by_name(name: str, redis=Depends(get_redis_client)):
    cache_key = movie_detail_key(name)

    cached = await cache_get_json(redis, cache_key)
    if cached is not None:
        return {"status": "Success", "data": cached}

    result = get_movie_by_slug_from_es(name)
    if result:
        serializable_data = jsonable_encoder(result)
        await cache_set_json(redis, cache_key, serializable_data, expire=300)
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
        celery_instance.send_task(_TASK_SYNC_MOVIE, args=[result.id], queue="light_queue")
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

        write_audit_log(                     
            action="UPDATE",
            admin_id=current_user_id,
            movie_id=result.id,
            movie_title=result.name,
            new_values=updateMovieDTO.model_dump()
        )
        celery_instance.send_task(
            _TASK_SYNC_MOVIE,
            args=[result.id],
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
    redis=Depends(get_redis_client),
):
    result = await patchMovieService.patch_movie(id, update_batch_movie)
    if result:
        background_tasks.add_task(cache_delete, redis, movie_detail_key(result.slug_name))

        write_audit_log(                     
            action="PATCH",
            admin_id=current_user_id,
            movie_id=result.id,
            movie_title=result.name,
            new_values=update_batch_movie.model_dump()
        )
        celery_instance.send_task(
            _TASK_SYNC_MOVIE,
            args=[result.id],
            queue="light_queue"
        )
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

    write_audit_log(                     
        action="DELETE",
        admin_id=current_user_id,
        movie_id=result.id,
        movie_title=result.name,
        new_values={}
    )
    if result:
        background_tasks.add_task(cache_delete, redis, movie_detail_key(result.slug_name))
        celery_instance.send_task(_TASK_DEL_MOVIE, args=[id], queue="light_queue")
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