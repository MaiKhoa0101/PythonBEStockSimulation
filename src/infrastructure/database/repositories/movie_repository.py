from src.infrastructure.database.utils.mapping import entity_to_model, model_to_entity
from src.presentation.dtos.movie_dto import MovieCreateDTO
from src.domain.entities.movies.movie import Movie
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
            Movie(
                id=db_movie.id,
                name=db_movie.name,
                slug_name=db_movie.slug_name,
                is_series=db_movie.is_series,
                description=db_movie.description,
                poster_url=db_movie.poster_url,
                thumb_url=db_movie.thumb_url,
                
                created_at=db_movie.created_at,
                updated_at=db_movie.updated_at,
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
        return db_movie
    
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
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.id == movie_entity.id,
            MovieModel.is_deleted == False
        ).first()
        if not db_movie:
            return None
        valid_columns = {col.key for col in sa_inspect(MovieModel).mapper.column_attrs}
        exclude = {"id", "created_at", "updated_at"}

        from dataclasses import asdict
        for k, v in asdict(movie_entity).items():
            if k in valid_columns and k not in exclude and v is not None:
                setattr(db_movie, k, v)

        if movie_entity.episodes:
            await self.upsert_episode(movie_entity)

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
        episode_id:str,
        path:str
    ):
        try:
            episode= self.db.query(EpisodeModel).filter(EpisodeModel.episode_id==episode_id).first()
            if not episode:
                return False
            episode.link_video = path
            self.db.commit()
            return True
        except any as e:
            self.db.rollback()
            raise Exception(f"Lỗi Database: {str(e)}")