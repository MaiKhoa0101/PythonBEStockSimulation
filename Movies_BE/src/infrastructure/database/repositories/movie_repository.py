import httpx
from src.domain.entities.movie import Movie
from src.infrastructure.database.models.movie_model import MovieModel
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from sqlalchemy.orm import Session

class MoviesRepositories(IMoviesRepository):
    def __init__(self, db: Session): 
        self.db = db
    
    
    async def fetch_movies_list(self):
        # Lúc này self.db mới thực sự là SQLAlchemy Session
        print ("Vào được repo")
        db_movie = self.db.query(MovieModel).all() 
        return db_movie
    
    async def fetch_movie_detail_by_name(self, name: str):
        
        db_movie = self.db.query(MovieModel).filter(MovieModel.slug_name == name).first()
        return db_movie
    
    async def fetch_movie_detail_by_id(self, id: str):
        
        db_movie = self.db.query(MovieModel).filter(MovieModel.id == id).first()
        return db_movie

