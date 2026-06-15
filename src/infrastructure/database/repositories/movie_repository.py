from typing import List
from dataclasses import asdict

from src.infrastructure.database.utils.mapping import entity_to_model, model_to_entity
from src.presentation.dtos.movie_dto import MovieCreateDTO
from src.domain.entities.movies.movie import Episode, Movie
from src.infrastructure.database.models.movies.movie_model import EpisodeModel, MovieModel
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import inspect as sa_inspect

class MoviesRepositories(IMoviesRepository):
    def __init__(self, db: Session): 
        self.db = db
    
    async def fetch_movies_list(self):
        db_movies = self.db.query(MovieModel).filter(
            MovieModel.is_deleted == False
        ).all() 
        result = [
            model_to_entity(
                db_movie,
                Movie
            )
            for db_movie in db_movies
        ]
        
        return result
    
    async def fetch_movie_detail_by_name(self, name: str):
        db_movie = self.db.query(MovieModel).options(
            joinedload(MovieModel.actors),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.countries),
            joinedload(MovieModel.categories),
            joinedload(MovieModel.episodes)
        ).filter(
            MovieModel.slug_name == name,
            MovieModel.is_deleted == False
        ).first()

        result = model_to_entity(
            db_movie,
            Movie
        )
        print("result truoc khi bien doi: ", result.episodes)
        if result.episodes:
            for episode in result.episodes:
                print("Sua episode: ",episode)
                episode.link_m3u8 = None
        return result
    
    async def fetch_movie_detail_by_name_no_auth(self, name: str):
        db_movie = self.db.query(MovieModel).options(
            joinedload(MovieModel.actors),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.countries),
            joinedload(MovieModel.categories),
            joinedload(MovieModel.episodes)
        ).filter(
            MovieModel.slug_name == name,
            MovieModel.is_deleted == False
        ).first()

        result = model_to_entity(
            db_movie,
            Movie
        )
        result.episodes = None
        return result

    async def fetch_movie_detail_by_id(self, id: str):
        db_movie = self.db.query(MovieModel).options(
            joinedload(MovieModel.actors),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.countries),
            joinedload(MovieModel.categories),
            joinedload(MovieModel.episodes)
        ).filter(
            MovieModel.id == id,
            MovieModel.is_deleted == False
        ).first()
        return db_movie

    async def create_movie(self, movie_entity: Movie) -> Movie:
        print(f"Gọi create repo với {movie_entity}")
        
        # 1. Map từ Entity sang Database Model
        db_movie = entity_to_model(
            movie_entity, 
            MovieModel,
            exclude={"id", "created_at", "updated_at", "episodes", "actors", "directors", "categories", "countries", "external_ids"}
        )

        for ep_entity in movie_entity.episodes:
            db_episode = entity_to_model(ep_entity, EpisodeModel, exclude={"id", "id_movie", "created_at", "updated_at"})
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

    async def update_entire_movie(self, movie_entity: Movie):
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.id == movie_entity.id,
            MovieModel.is_deleted == False
        ).first()
        if not db_movie:
            return None

        valid_columns = {col.key for col in sa_inspect(MovieModel).mapper.column_attrs}
        exclude = {"id", "created_at", "updated_at", "episodes", "actors", "directors", "categories", "countries", "external_ids"}
        
        from dataclasses import asdict
        for k, v in asdict(movie_entity).items():
            if k in valid_columns and k not in exclude:
                setattr(db_movie, k, v)

        db_movie.episodes = [
            entity_to_model(ep, EpisodeModel, exclude={"id", "id_movie", "created_at", "updated_at"})
            for ep in movie_entity.episodes
        ]

        self.db.commit()
        self.db.refresh(db_movie)

        movie_entity.id = db_movie.id
        movie_entity.created_at = db_movie.created_at
        movie_entity.updated_at = db_movie.updated_at

        return movie_entity
        
    async def patch_movie(self, movie_entity):
        try:
            db_movie = self.db.query(MovieModel).filter(
                MovieModel.id == movie_entity.id,
                MovieModel.is_deleted == False
            ).first()
            if not db_movie:
                return None

            valid_columns = {col.key for col in sa_inspect(MovieModel).mapper.column_attrs}
            exclude = {"id", "created_at", "updated_at"}

            for k, v in asdict(movie_entity).items():
                if k in valid_columns and k not in exclude and v is not None:
                    setattr(db_movie, k, v)

            if movie_entity.episodes is not None:
                await self._replace_episodes(db_movie, movie_entity.episodes)
            self.db.commit()
            self.db.refresh(db_movie)

            movie_entity.id = db_movie.id
            movie_entity.created_at = db_movie.created_at
            movie_entity.updated_at = db_movie.updated_at
    
            return movie_entity

        except Exception as e:
            self.db.rollback() 
            raise Exception(f"Lỗi patch movie: {str(e)}")


    async def _replace_episodes(self, db_movie: MovieModel, new_episodes: List[Episode]) -> None:
        self.db.query(EpisodeModel).filter(
            EpisodeModel.id_movie == db_movie.id
        ).delete(synchronize_session=False)

        for ep in new_episodes:
            db_ep = EpisodeModel(
                id_movie=db_movie.id,
                name_episode=ep.name_episode,
                slug=ep.slug,
                filename=ep.filename,
                link_embed=ep.link_embed,
                link_m3u8=ep.link_m3u8,
                server_name=ep.server_name,
                description=ep.description,
            )
            self.db.add(db_ep)
            
    async def upsert_episode(self, movie_entity):
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.id == movie_entity.id,
            MovieModel.is_deleted == False
        ).first()
        
        if movie_entity.episodes:
            for episode in movie_entity.episodes:
                existed_ep = None

                for db_ep in db_movie.episodes:
                    if (episode.id and episode.id == db_ep.id) or (episode.slug and episode.slug == db_ep.slug):
                        existed_ep = db_ep
                        break  # ← đúng chỗ
                
                
                if existed_ep:
                    if episode.name_episode:
                        existed_ep.name_episode = episode.name_episode
                    if episode.slug:
                        existed_ep.slug = episode.slug
                    if episode.link_embed:
                        existed_ep.link_embed = episode.link_embed
                    if episode.link_m3u8:
                        existed_ep.link_m3u8 = episode.link_m3u8
                    if episode.server_name:
                        existed_ep.server_name = episode.server_name
                    if episode.description:
                        existed_ep.description = episode.description
                else:
                    existed_ep = EpisodeModel(
                        name_episode=episode.name_episode,
                        slug=episode.slug,
                        filename=episode.filename,
                        link_embed=episode.link_embed,
                        link_m3u8=episode.link_m3u8,
                        server_name=episode.server_name,
                        description=episode.description,
                    )
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
    
    async def upload_episode(
        self,
        episode_id: str,
        path: str,
        is_hls: bool = False         
    ):
        try:
            episode = self.db.query(EpisodeModel).filter(
                EpisodeModel.id == episode_id
            ).first()

            if not episode:
                return False

            if is_hls:
                episode.link_m3u8 = path   
            else:
                episode.link_embed = path 

            self.db.commit()
            return True

        except Exception as e:            
            self.db.rollback()
            raise Exception(f"Lỗi Database: {str(e)}")
        
    async def get_url_episode(self, id_episode: str):
        db_episode = self.db.query(EpisodeModel).filter(
            EpisodeModel.id == id_episode
        ).first()

        return {
            "url": db_episode.link_m3u8,
            "movie_id": db_episode.id_movie
        }