from typing import List, Optional
from dataclasses import asdict

from src.infrastructure.database.models.imdb.imdb import MovieExternalIdsModel
from src.infrastructure.database.models.country.country import CountryModel
from src.infrastructure.database.utils.mapping import entity_to_model, model_to_entity
from src.presentation.dtos.movie_dto import MovieCreateDTO
from src.domain.entities.movies.movie import Episode, Movie
from src.infrastructure.database.models.movies.movie_model import EpisodeModel, MovieModel
from src.infrastructure.database.models.categories.categories import CategoryModel
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import inspect as sa_inspect, or_, and_

class MoviesRepositories(IMoviesRepository):
    def __init__(self, db: Session): 
        self.db = db

    def _resolve_categories(self, category_ids: List[str]) -> List["CategoryModel"]:
        """Query CategoryModel theo danh sách id. category_ids rỗng -> trả [] (bỏ hết category)."""
        if not category_ids:
            return []
        return (
            self.db.query(CategoryModel)
            .filter(CategoryModel.id.in_(category_ids))
            .all()
        )

    def _resolve_countries(self, country_ids: List[str]) -> List["CountryModel"]:
        """Tương tự _resolve_categories nhưng cho Country — TRƯỚC ĐÂY KHÔNG TỒN TẠI,
        khiến create_movie không bao giờ gán được country cho phim (bug #2)."""
        if not country_ids:
            return []
        return (
            self.db.query(CountryModel)
            .filter(CountryModel.id.in_(country_ids))
            .all()
        )

    # ── Dùng riêng cho luồng sync từ nguồn ngoài (phimapi...) ────────────────
    # Khác _resolve_categories/_resolve_countries (chỉ lookup, dùng cho luồng
    # admin tạo/sửa phim tay — FE luôn gửi id nội bộ có sẵn), 2 hàm dưới đây
    # nhận list {"name":..., "slug":...} thô từ API ngoài, TỰ TẠO MỚI record
    # nếu slug chưa có trong DB, rồi trả về id nội bộ tương ứng.
    async def get_or_create_categories(self, categories: List[dict]) -> List[str]:
        if not categories:
            return []
        slugs = [c["slug"] for c in categories if c.get("slug")]
        if not slugs:
            return []
        existed = (
            self.db.query(CategoryModel)
            .filter(CategoryModel.slug.in_(slugs))
            .all()
        )
        existed_by_slug = {c.slug: c for c in existed}

        result_ids: List[str] = []
        for c in categories:
            slug = c.get("slug")
            if not slug:
                continue
            model = existed_by_slug.get(slug)
            if not model:
                model = CategoryModel(name=c.get("name") or slug, slug=slug)
                self.db.add(model)
                self.db.flush()  # cần id ngay để dùng, chưa commit vội
                existed_by_slug[slug] = model
            result_ids.append(model.id)
        return result_ids

    async def get_or_create_countries(self, countries: List[dict]) -> List[str]:
        if not countries:
            return []
        slugs = [c["slug"] for c in countries if c.get("slug")]
        if not slugs:
            return []
        existed = (
            self.db.query(CountryModel)
            .filter(CountryModel.slug.in_(slugs))
            .all()
        )
        existed_by_slug = {c.slug: c for c in existed}

        result_ids: List[str] = []
        for c in countries:
            slug = c.get("slug")
            if not slug:
                continue
            model = existed_by_slug.get(slug)
            if not model:
                model = CountryModel(name=c.get("name") or slug, slug=slug)
                self.db.add(model)
                self.db.flush()
                existed_by_slug[slug] = model
            result_ids.append(model.id)
        return result_ids

    async def find_movie_id_by_slug(self, slug_name: str) -> Optional[str]:
        """Check tồn tại theo slug_name (UNIQUE) — dùng để task sync biết phim
        đã có hay chưa mà không cần load hết relationship như fetch_movie_detail_by_name."""
        row = (
            self.db.query(MovieModel.id)
            .filter(MovieModel.slug_name == slug_name, MovieModel.is_deleted == False)
            .first()
        )
        return row[0] if row else None
    
    async def fetch_movies_list(
        self,
        page: int = 1,
        size: int = 20,
        q: Optional[str] = None,
        category_id: Optional[str] = None,
        country_slug: Optional[str] = None,
        status: Optional[str] = None,
        is_series: Optional[bool] = None,
        quality: Optional[str] = None,
        year: Optional[int] = None,
    ) -> dict:
        query = self.db.query(MovieModel).filter(
            MovieModel.is_deleted == False
        )

        conditions = []

        if q and q.strip():
            search_pattern = f"%{q.strip()}%"
            conditions.append(
                or_(
                    MovieModel.name.ilike(search_pattern),        # Tìm theo tên tiếng Việt
                    MovieModel.origin_name.ilike(search_pattern)  # Tìm theo tên gốc
                )
            )

        if category_id:
            # .any() trên relationship many-to-many -> EXISTS subquery, tránh
            # JOIN trực tiếp có thể sinh trùng dòng nếu phim khớp nhiều điều kiện.
            conditions.append(MovieModel.categories.any(CategoryModel.id == category_id))

        if country_slug:
            conditions.append(MovieModel.countries.any(CountryModel.slug == country_slug))

        if status:
            conditions.append(MovieModel.status == status)

        if is_series is not None:
            conditions.append(MovieModel.is_series == is_series)

        if quality:
            conditions.append(MovieModel.quality == quality)

        if year is not None:
            conditions.append(MovieModel.year == year)

        if conditions:
            query = query.filter(and_(*conditions))

        # total PHẢI tính sau khi đã áp hết filter ở trên, nếu không phân
        # trang sẽ tính sai tổng số trang so với kết quả thực tế trả về.
        total = query.count()

        db_movies = (
            query
            .order_by(MovieModel.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        results = [
            model_to_entity(
                db_movie,
                Movie
            )
            for db_movie in db_movies
        ]

        return {"total": total, "page": page, "size": size, "results": results}
    

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
        print("Goi get no auth")
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

    async def create_movie(self, movie_entity: Movie, category_ids: List[str] = None, country_ids: List[str] = None) -> Movie:
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

        # Gán categories/countries: *_ids lấy trực tiếp từ DTO ở tầng service, truyền
        # riêng xuống đây (không đi qua entity) vì entity chỉ giữ full Category/Country object.
        db_movie.categories = self._resolve_categories(category_ids)
        db_movie.countries = self._resolve_countries(country_ids)  # (bug #2) trước đây bị bỏ sót hoàn toàn

        # (bug #3) external_ids trước đây bị exclude khi map + không có chỗ nào tạo
        # MovieExternalIdsModel — dữ liệu tmdb/imdb nhập vào bị rơi mất im lặng.
        if movie_entity.external_ids:
            db_movie.external_ids = entity_to_model(
                movie_entity.external_ids,
                MovieExternalIdsModel,
                exclude={"id", "id_movie"},
            )

        # 2. Lưu xuống MySQL
        self.db.add(db_movie)
        self.db.commit()
        self.db.refresh(db_movie)

        # (bug #5) movie_entity.id vẫn là "" (giá trị override lúc tạo entity) nếu
        # không gán lại ở đây — khiến fetch_movie_detail_by_id bên dưới tìm theo id
        # rỗng và luôn trả None dù insert đã thành công. update_entire_movie đã làm
        # đúng việc gán lại này, create_movie thì thiếu.
        movie_entity.id = db_movie.id

        return await self.fetch_movie_detail_by_id(movie_entity.id)

    async def update_entire_movie(self, movie_entity: Movie, category_ids: List[str] = None):
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

        # PUT = thay thế toàn bộ category hiện có bằng category_ids mới gửi lên
        db_movie.categories = self._resolve_categories(category_ids)

        self.db.commit()
        self.db.refresh(db_movie)

        movie_entity.id = db_movie.id
        movie_entity.created_at = db_movie.created_at
        movie_entity.updated_at = db_movie.updated_at

        return await self.fetch_movie_detail_by_id(movie_entity.id)
        
    async def patch_movie(self, movie_entity, category_ids: List[str] = None):
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
                await self.upsert_episode(movie_entity)

            # PATCH = chỉ đụng vào category khi FE thực sự gửi category_ids
            # (None nghĩa là FE không gửi field này, giữ nguyên category cũ)
            if category_ids is not None:
                db_movie.categories = self._resolve_categories(category_ids)

            self.db.commit()
            self.db.refresh(db_movie)

            return await self.fetch_movie_detail_by_id(movie_entity.id)

        except Exception as e:
            self.db.rollback() 
            raise Exception(f"Lỗi patch movie: {str(e)}")


            
    async def upsert_episode(self, movie_entity):
        db_movie = self.db.query(MovieModel).filter(
            MovieModel.id == movie_entity.id,
            MovieModel.is_deleted == False
        ).first()
        
        if movie_entity.episodes:
            for episode in movie_entity.episodes:
                existed_ep = None

                for db_ep in db_movie.episodes:
                    # (fix) match chỉ theo slug bị đụng hàng khi 1 phim có NHIỀU
                    # SERVER (VD: Vietsub + Thuyết Minh) — mỗi server đều đánh số
                    # tập lại từ "tap-1", nên slug KHÔNG unique nếu thiếu server_name
                    # đi kèm. Trước đây match sai sẽ khiến 2 server ghi đè lẫn nhau.
                    same_id = episode.id and episode.id == db_ep.id
                    same_slug_and_server = (
                        episode.slug and episode.slug == db_ep.slug
                        and episode.server_name == db_ep.server_name
                    )
                    if same_id or same_slug_and_server:
                        existed_ep = db_ep
                        break
                
                
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

        db_movie.is_deleted = True
        self.db.commit()
        self.db.refresh(db_movie)  

        result = model_to_entity(
            db_movie,
            Movie
        )
        return result
    
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
        print ("Gọi get_url_episode với id_episode: ", id_episode)
        db_episode = self.db.query(EpisodeModel).filter(
            EpisodeModel.id == id_episode
        ).first()

        return {
            "url": db_episode.link_m3u8,
            "movie_id": db_episode.id_movie
        }