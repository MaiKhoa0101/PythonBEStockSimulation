from src.infrastructure.database.utils.mapping import dto_to_entity
from src.domain.entities.movies.movie import Episode, Movie
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import IUpdateEntireMovie


class UpdateEntireMovie(IUpdateEntireMovie):
    def __init__(self, movie_repository: IMoviesRepository):
        self.movie_repository = movie_repository
    
    async def update_entire_movie(self, id: str, movie_data):
        existing_movie = await self.movie_repository.fetch_movie_detail_by_id(id)
        if not existing_movie:
            return None

        episode_entities = [
            dto_to_entity(ep, Episode, overrides={"id": "", "id_movie": id})
            for ep in movie_data.episodes
        ]
        movie_entity = dto_to_entity(
            movie_data,
            Movie,
            exclude={"episodes"},
            overrides={"id": id, "episodes": episode_entities}
        )
        updated = await self.movie_repository.update_entire_movie(
            movie_entity=movie_entity,
            category_ids=movie_data.category_ids,  # lấy trực tiếp từ DTO, không qua entity
        )
        return updated or None