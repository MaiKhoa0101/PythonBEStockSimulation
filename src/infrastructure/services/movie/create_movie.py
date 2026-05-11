

from src.domain.entities.movies.movie import Episode, Movie
from src.presentation.dtos.movie_dto import MovieCreateDTO
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import ICreateMovie
from src.domain.entities.movies.movie import Episode, Movie
from src.presentation.dtos.movie_dto import MovieCreateDTO
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import ICreateMovie
from src.infrastructure.database.utils.mapping import dto_to_entity


class CreateMovie(ICreateMovie):
    def __init__(self, movie_repository: IMoviesRepository):
        self.movie_repository = movie_repository

    async def create_movie(self, movie_data: MovieCreateDTO):
        episode_entities = [
            dto_to_entity(ep, Episode, overrides={"id": "", "id_movie": ""})
            for ep in movie_data.episodes
        ]
        new_movie_entity = dto_to_entity(
            movie_data,
            Movie,
            exclude={"episodes"},
            overrides={"id": "", "episodes": episode_entities}
        )
        created = await self.movie_repository.create_movie(movie_entity=new_movie_entity)
        return created or None