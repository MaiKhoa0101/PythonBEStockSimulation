from typing import Protocol, Any

from src.presentation.dtos.movie_dto import MovieCreateDTO, MoviePatchDTO, MovieUpdateDTO 

class IGetListMoviesService(Protocol): 
    async def fetch_movies_list() -> Any:
        ... 
class IGetMoviesDetailByName(Protocol):
    async def fetch_movie_detail_by_name(name: str) -> Any:
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
