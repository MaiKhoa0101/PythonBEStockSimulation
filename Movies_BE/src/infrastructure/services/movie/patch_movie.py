from src.domain.entities.movies.movie import Episode, Movie
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.presentation.dtos.movie_dto import MoviePatchDTO
from src.application.interfaces.services.movies_service_interface import IPatchMovie


class PatchMovie(IPatchMovie):

    def __init__(
        self,
        movie_repository: IMoviesRepository
    ):
        self.movie_repository= movie_repository
        
    async def patch_movie(self,id:str, movie_data:MoviePatchDTO):

        existing_movie= await self.movie_repository.fetch_movie_detail_by_id(id)
        if not existing_movie:
            return None
        if movie_data.episodes:
            for episode in movie_data.episodes:
                ep_entity = Episode(
                    id="",
                    id_movie=id,
                    name_episode=episode.name_episode,
                    link_video=episode.link_video,
                    description=episode.description
                )
                episode_entities.append(ep_entity)
        
        existing_movie = Movie(
            id= id, 
            slug_name=movie_data.slug_name,
            is_series=movie_data.is_series,
            name=movie_data.name,
            description=movie_data.description,
            episodes=episode_entities
        )
        updated_movie_entity = await self.movie_repository.patch_movie(
            movie_entity=existing_movie
        )

        if not updated_movie_entity: #ko thanh cong
            return None
        return updated_movie_entity

   