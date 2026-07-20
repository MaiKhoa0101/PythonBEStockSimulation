from src.domain.entities.movies.movie import Episode, Movie
from src.domain.entities.imdb.imdb import MovieExternalIds
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

        external_ids_entity = (
            dto_to_entity(movie_data.external_ids, MovieExternalIds, overrides={"id": "", "id_movie": ""})
            if movie_data.external_ids
            else None
        )

        new_movie_entity = dto_to_entity(
            movie_data,
            Movie,
            exclude={"episodes", "external_ids"},
            overrides={"id": "", "episodes": episode_entities, "external_ids": external_ids_entity}
        )

        created = await self.movie_repository.create_movie(
            movie_entity=new_movie_entity,
            category_ids=movie_data.category_ids,
            country_ids=movie_data.country_ids,
        )
        return created or None