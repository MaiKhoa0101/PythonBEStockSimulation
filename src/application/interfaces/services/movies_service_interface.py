from typing import Protocol, Any

from fastapi import BackgroundTasks, UploadFile

from src.domain.entities.movies.movie import Movie
from src.presentation.dtos.movie_dto import MovieCreateDTO, MoviePatchDTO, MovieUpdateDTO 

class IGetListMoviesService(Protocol): 
    #ep kieu tra ve
    async def fetch_movies_list() -> list[Movie]:
        ... 
class IGetMoviesDetailByName(Protocol):
    async def fetch_movie_detail_by_name(name: str, current_user_id:str) -> Any:
        ...

class IGetMoviesDetailById(Protocol):
    async def fetch_movie_detail_by_id(id: str) -> Any:
        ...

class ICreateMovie(Protocol):
    async def create_movie(movie_data:MovieCreateDTO):
        ...

class IUpdateEntireMovie(Protocol):
    async def update_entire_movie(id:str , movie_data: MovieUpdateDTO):
        ...

class IPatchMovie(Protocol):
    async def patch_movie(id:str ,movie_data: MoviePatchDTO):
        ...

class IDeleteMovie(Protocol):
    async def delete_movie_by_id(id:str):
        ...

class IUploadEpisode(Protocol):
    async def upload_episode_video_into_local_system_path(movie_slug: str, episode_id: str, file: UploadFile) -> str:
        ...

    async def upload_episode_video_hls(movie_slug: str, episode_id: str, file: UploadFile, bg_tasks: BackgroundTasks) -> str:
        ...