from typing import Protocol, Any

from src.application.dtos.movie_dto import MovieCreateDTO 

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