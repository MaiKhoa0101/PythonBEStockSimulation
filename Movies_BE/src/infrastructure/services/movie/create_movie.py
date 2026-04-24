

from src.domain.entities.movie import Episode, Movie
from src.application.dtos.movie_dto import MovieCreateDTO
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import ICreateMovie


class CreateMovie(ICreateMovie):
    def __init__(
        self,
        movie_repository: IMoviesRepository
    ):
        self.movie_repository= movie_repository
        
    async def create_movie(self, movie_data: MovieCreateDTO):

        episode_entities = []
        for ep_dto in movie_data.episodes:
            ep_entity = Episode(
                id="", # Database tự sinh
                id_movie="", # Lát nữa MySQL tự móc khóa ngoại
                name_episode=ep_dto.name_episode,
                link_video=ep_dto.link_video,
                description=ep_dto.description
            )
            episode_entities.append(ep_entity)


        new_movie_entity = Movie(
            id="", 
            slug_name=movie_data.slug_name,
            is_series=movie_data.is_series,
            name=movie_data.name,
            description=movie_data.description,
            episodes=episode_entities
        )

        # 3. Ném ENTITY cho Repository (Không ném DTO nữa)
        created_movie_entity = await self.movie_repository.create_movie(
            movie_entity=new_movie_entity
        )
        print ("Kết quả ở service: ",created_movie_entity)
        return created_movie_entity