from src.domain.entities.movie import Episode, Movie
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import IUpdateEntireMovie


class UpdateEntireMovie(IUpdateEntireMovie):
    def __init__(
        self,
        movie_repository: IMoviesRepository
    ):
        self.movie_repository= movie_repository

    async def update_entire_movie(self, id, movie_data):
        print ("Vào được update")
        #1. Lấy dữ liệu phim trong database coi có tồn tại chưa
        existing_movie= await self.movie_repository.fetch_movie_detail_by_id(id)
        if not existing_movie:
            raise Exception("Movie not found")
        
        episode_entities = []

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
        print ("đi tới đây")

        # Update len repository
        updated_movie_entity = await self.movie_repository.update_entire_movie(
            movie_entity=existing_movie
        )
        return updated_movie_entity

        # # 1. Lấy dữ liệu phim hiện tại từ database thông qua Repository
        # existing_movie = await self.movie_repository.fetch_movie_detail_by_id(movie_data.id)
        # if not existing_movie:
        #     raise Exception("Movie not found")

        # # 2. Cập nhật toàn bộ thông tin của phim với dữ liệu mới từ DTO
        # existing_movie.name = movie_data.name
        # existing_movie.slug_name = movie_data.slug_name
        # existing_movie.is_series = movie_data.is_series
        # existing_movie.description = movie_data.description

        # # Xóa hết các tập phim cũ đi (nếu có) và thêm các tập phim mới vào
        # existing_movie.episodes.clear()
        # for ep_dto in movie_data.episodes:
        #     ep_entity = Episode(
        #         id="", # Database tự sinh
        #         id_movie=existing_movie.id, # Gán khóa ngoại đúng
        #         name_episode=ep_dto.name_episode,
        #         link_video=ep_dto.link_video,
        #         description=ep_dto.description
        #     )
        #     existing_movie.episodes.append(ep_entity)

        # # 3. Gọi Repository để lưu lại thông tin đã cập nhật vào database
        # updated_movie_entity = await self.movie_repository.update_entire_movie(
        #     movie_entity=existing_movie
        # )

        # return updated_movie_entity