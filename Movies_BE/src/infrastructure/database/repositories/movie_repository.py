import httpx
from src.application.dtos.movie_dto import MovieCreateDTO
from src.domain.entities.movie import Movie
from src.infrastructure.database.models.movie_model import EpisodeModel, MovieModel
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from sqlalchemy.orm import Session

class MoviesRepositories(IMoviesRepository):
    def __init__(self, db: Session): 
        self.db = db
    
    
    async def fetch_movies_list(self):
        print ("Vào được repo")
        db_movies = self.db.query(MovieModel).all() 
        result = [
            Movie(
                id=db_movie.id,
                name=db_movie.name,
                slug_name=db_movie.slug_name,
                is_series=db_movie.is_series,
                description=db_movie.description,
                
                created_at=db_movie.created_at,
                created_by=db_movie.created_by,
                updated_at=db_movie.updated_at,
                updated_by=db_movie.updated_by
            )
            for db_movie in db_movies
        ]
        
        return result
    
    async def fetch_movie_detail_by_name(self, name: str):
        
        db_movie = self.db.query(MovieModel).filter(MovieModel.slug_name == name).first()
        return db_movie
    
    async def fetch_movie_detail_by_id(self, id: str):
        
        db_movie = self.db.query(MovieModel).filter(MovieModel.id == id).first()
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
