import httpx
from src.presentation.dtos.movie_dto import MovieCreateDTO
from src.domain.entities.movie import Movie
from src.infrastructure.database.models.movie_model import EpisodeModel, MovieModel
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from sqlalchemy.orm import Session

class MoviesRepositories(IMoviesRepository):
    def __init__(self, db: Session): 
        self.db = db
    
    
    async def fetch_movies_list(self):
        db_movies = self.db.query(MovieModel).filter(
            MovieModel.is_deleted == False
        ).all() 
        result = [
            Movie(
                id=db_movie.id,
                name=db_movie.name,
                slug_name=db_movie.slug_name,
                is_series=db_movie.is_series,
                description=db_movie.description,
                
                created_at=db_movie.created_at,
                updated_at=db_movie.updated_at,
            )
            for db_movie in db_movies
        ]
        
        return result
    
    async def fetch_movie_detail_by_name(self, name: str):
        
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.slug_name == name,
            MovieModel.is_deleted == False
        ).first()
        return db_movie
    
    async def fetch_movie_detail_by_id(self, id: str):
        
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.id == id,
            MovieModel.is_deleted == False
        ).first()
        return db_movie

    async def create_movie(self, movie_entity: Movie) -> Movie:
        print(f"Gọi create repo với {movie_entity}")
        
        # 1. Map từ Entity sang Database Model
        db_movie = MovieModel(
            name=movie_entity.name,
            slug_name=movie_entity.slug_name,
            is_series=movie_entity.is_series,
            description=movie_entity.description
        )

        for ep_entity in movie_entity.episodes:
            db_episode = EpisodeModel(
                name_episode=ep_entity.name_episode,
                link_video=ep_entity.link_video,
                description=ep_entity.description
            )
            db_movie.episodes.append(db_episode)
        
        # 2. Lưu xuống MySQL
        self.db.add(db_movie)
        self.db.commit()
        self.db.refresh(db_movie)

        # 3. Cập nhật lại những thông tin tự sinh từ DB vào Entity hiện tại
        movie_entity.id = db_movie.id
        movie_entity.created_at = db_movie.created_at
        movie_entity.updated_at = db_movie.updated_at
        
        # 4. Trả Entity hoàn chỉnh ngược lên cho Service
        return movie_entity

    async def update_entire_movie(
        self,
        movie_entity:Movie
    ):     
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.id == movie_entity.id,
            MovieModel.is_deleted == False
        ).first()
        if not db_movie:
            return None
        
        db_movie.name = movie_entity.name
        db_movie.slug_name = movie_entity.slug_name
        db_movie.description = movie_entity.description
        db_movie.is_series = movie_entity.is_series
        db_movie.episodes = []
        for ep_entity in movie_entity.episodes:
            db_episode = EpisodeModel(
                name_episode = ep_entity.name_episode,
                description = ep_entity.description,
                link_video = ep_entity.link_video
            )
            db_movie.episodes.append(db_episode)
        
        self.db.commit()
        self.db.refresh(db_movie)

        movie_entity.id = db_movie.id
        movie_entity.created_at = db_movie.created_at
        movie_entity.updated_at = db_movie.updated_at
        
        return movie_entity
    
    async def patch_movie(self, movie_entity):
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.id == movie_entity.id,
            MovieModel.is_deleted == False
        ).first()
        if not db_movie:
            return None
        
        if movie_entity.description is not None:
            db_movie.description = movie_entity.description
        if movie_entity.name is not None:
            db_movie.name = movie_entity.name
        if movie_entity.slug_name is not None:
            db_movie.slug_name= movie_entity.slug_name
        if movie_entity.is_series is not None:
            db_movie.is_series = movie_entity.is_series
        if movie_entity.episodes != []:
            self.upsert_episode(movie_entity)
        self.db.commit()
        self.db.refresh(db_movie)

        movie_entity.id = db_movie.id
        movie_entity.created_at = db_movie.created_at
        movie_entity.updated_at = db_movie.updated_at
    
        return movie_entity

    
    async def upsert_episode(self, movie_entity):
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.id == movie_entity.id,
            MovieModel.is_deleted == False
        ).first()
        
        #check có cập nhật episode ko
        if movie_entity.episodes:
            # Lặp từng episode cập nhật
            for episode in movie_entity.episodes:
                existed_ep = None

                # check trong db, coi có trùng id hay name ko,
                # có thì sửa lên episode gốc
                # không thì tạo mới
                for db_ep in db_movie.episodes:
                    if (episode.id and episode.id == db_ep.id) or (episode.name and episode.name == db_ep.name):
                        existed_ep = db_ep
                    break
                
                
                if existed_ep:
                    if episode.name:
                        existed_ep.name= episode.name
                    if episode.description:
                        existed_ep.description = episode.description
                    if episode.link_video:
                        existed_ep.link_video = episode.link_video
                else:
                    existed_ep = episode
                
                db_movie.episodes.append(existed_ep)
        self.db.commit()

    async def delete_movie_by_id(self, id):
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.id == id,
            MovieModel.is_deleted == False 
        ).first()

        if not db_movie:   
            return None
        
        db_movie.is_deleted=True

        self.db.commit()

        return True

