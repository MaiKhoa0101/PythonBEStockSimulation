from fastapi import APIRouter, BackgroundTasks, Depends, File, Path, UploadFile

from src.presentation.dtos.short_dto import ShortCreateDTO
from src.application.interfaces.services.short_service_interface import IShortService
from src.infrastructure.security.security import get_current_user_id
from src.presentation.dtos.movie_dto import MovieCreateDTO, MoviePatchDTO, MovieUpdateDTO
from src.domain.entities.movies.movie import Movie
from src.application.interfaces.services.movies_service_interface import IGetListMoviesService, IGetMoviesDetailById, IGetMoviesDetailByName, ICreateMovie, IPatchMovie, IUpdateEntireMovie, IUploadEpisode
from src.presentation.controller.dependencies import IShortServiceDependency, IUploadEpisodeServiceDepedency

router = APIRouter()

@router.post("/create")
async def api_create_short(
    bg_tasks: BackgroundTasks,
    movie_id: str ,
    episode_id: str,

    title: str,
    start_time: int,
    duration: int,
    
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id),
    shortService: IShortService = Depends(IShortServiceDependency),
    upload_service: IUploadEpisode = Depends(IUploadEpisodeServiceDepedency)
):
    result_path = await upload_service.upload_episode_video_hls(
       first_folder= movie_id, 
       episode_slug= episode_id, 
       file= file, 
       bg_tasks =bg_tasks, 
       is_short = True
    )
    
    short_data = ShortCreateDTO(
        movie_id=movie_id,
        episode_id=episode_id,
        title=title,
        start_time=start_time,
        duration=duration,
        video_url=result_path,
        user_id=current_user_id
    )
    
    result = await shortService.create_short(short_data)
    
    if result:
        return {"status": "Success", "data": result}
    return {"status": "Failed", "data": "Update không thành công"}

@router.get("/shorts_list/")
async def api_get_shorts_list(
    shortService: IShortService = Depends(IShortServiceDependency)
):
    print("Vào tới controller")
    result = await shortService.get_shorts()
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
    

@router.get("/shorts_list_by_id")
async def api_get_shorts_list_by_id(
    current_user_id: str = Depends(get_current_user_id),
    shortService: IShortService = Depends(IShortServiceDependency)
):
    print("Vào tới controller")
    result = await shortService.get_shorts(current_user_id)
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
    
    
@router.get("movie/{id}")
async def api_get_shorts_by_movie_id(
    id:str=None,
    shortService: IShortService = Depends(IShortServiceDependency)
):
    result = await shortService.get_shorts_by_movie_id(id)
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
    

@router.get("episode/{id}")
async def api_get_shorts_by_episode_id(
    id:str=None,
    shortService: IShortService = Depends(IShortServiceDependency)
):
    result = await shortService.get_shorts_by_episode_id(id)
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
    
@router.get("/{id}")
async def api_get_shorts_by_self_id(
    id:str=None,
    shortService: IShortService = Depends(IShortServiceDependency)
):
    result = await shortService.get_short_by_self_id(id)
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
    
@router.get("user/{id}")
async def api_get_shorts_by_user_id(
    current_user_id: str = Depends(get_current_user_id),
    shortService: IShortService = Depends(IShortServiceDependency)
):
    result = await shortService.get_shorts_by_user_id(current_user_id)
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

@router.delete("/{id}")
async def api_delete_short(
    id:str=None,
    shortService: IShortService = Depends(IShortServiceDependency)
):
    result = await shortService.delete_short(id)
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



