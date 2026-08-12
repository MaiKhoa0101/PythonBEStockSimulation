from typing import Optional, Protocol, Any

from fastapi import BackgroundTasks, UploadFile

from src.domain.entities.movies.movie import Movie
from src.presentation.dtos.movie_dto import MovieCreateDTO, MoviePatchDTO, MovieUpdateDTO 

class IGetListMoviesService(Protocol): 
    #ep kieu tra ve
    async def fetch_movies_list(page:int , size:int, q: Optional[str] = None) -> list[Movie]:
        ... 
class IGetMoviesDetailByName(Protocol):
    async def fetch_movie_detail_by_name(self,name: str) -> Any:
        ...

class IGetMoviesDetailById(Protocol):
    async def fetch_movie_detail_by_id(self,id: str) -> Any:
        ...

class ICreateMovie(Protocol):
    async def create_movie(self,movie_data:MovieCreateDTO):
        ...

class IUpdateEntireMovie(Protocol):
    async def update_entire_movie(self,id:str , movie_data: MovieUpdateDTO):
        ...

class IPatchMovie(Protocol):
    async def patch_movie(self,id:str ,movie_data: MoviePatchDTO):
        ...

class IDeleteMovie(Protocol):
    async def delete_movie_by_id(self,id:str):
        ...
        
class IGetVideoUrlService(Protocol):
    async def get_video_url(
        self,
        id_episode:str
    ):
        ...

class IUploadEpisode(Protocol):
    async def upload_episode_video_into_local_system_path(self, movie_slug: str, episode_id: str, file: UploadFile) -> str:
        ...

    async def upload_episode_video_hls( 
        self,
        first_folder: str, 
        episode_slug: str, 
        file: UploadFile, 
        bg_tasks: BackgroundTasks,
        is_short:bool
    ) -> str:
        ...


class IHabitSimilarMoviesService(Protocol):
    async def get_habit_similar_movies(self, movie_id: str, limit: int = 5):
        ...