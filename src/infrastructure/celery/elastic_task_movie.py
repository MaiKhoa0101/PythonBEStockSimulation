from src.infrastructure.elasticsearch.es_client import es_client, MOVIE_INDEX, recreate_movie_index
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.models.movies.movie_model import MovieModel
from src.infrastructure.celery.celery_app import celery_instance
from elasticsearch.helpers import bulk
from sqlalchemy.orm import joinedload, subqueryload
def _actor_to_es(actor) -> dict:
    return {
        "id": str(actor.id),
        "name": actor.name,
        "slug": getattr(actor, "slug", None),
    }


def _director_to_es(director) -> dict:
    return {
        "id": str(director.id),
        "name": director.name,
        "slug": getattr(director, "slug", None),
    }


def _category_to_es(category) -> dict:
    return {
        "id": str(category.id),
        "name": category.name,
        "slug": getattr(category, "slug", None),
    }


def _country_to_es(country) -> dict:
    return {
        "id": str(country.id),
        "name": country.name,
        "slug": getattr(country, "slug", None),
    }


def _build_movie_document(movie: MovieModel) -> dict:
    """
    Document builder DUY NHẤT — dùng chung cho cả sync-từng-phim và bulk-sync,
    tránh lệch schema giữa 2 đường đồng bộ (trước đây `countries` dùng .slug
    ở một chỗ và .name ở chỗ khác).

    FIX: actors/directors/categories/countries trước đây chỉ lưu `.name`
    (list[str]) khiến ES lệch pha với API list-movie (trả CategoryDTO/
    CountryDTO/ActorDTO/DirectorDTO đầy đủ id+name+slug). Giờ lưu full object
    {id, name, slug} cho cả 4 field để FE nhận dữ liệu đồng nhất dù đọc từ
    DB hay từ ES.
    """
    return {
        "id":           str(movie.id),
        "name":         movie.name,
        "origin_name":  movie.origin_name,
        "description":  movie.description,
        "actors":       [_actor_to_es(actor) for actor in movie.actors],
        "directors":    [_director_to_es(director) for director in movie.directors],
        "categories":   [_category_to_es(cat) for cat in movie.categories],
        "countries":    [_country_to_es(c) for c in movie.countries],
        "slug_name":    movie.slug_name,
        "poster_url":   movie.poster_url,
        "thumb_url":    movie.thumb_url,
        "year":         int(movie.year) if movie.year else None,
        "view":         int(movie.view) if movie.view else 0,
        "is_deleted":   movie.is_deleted,
        "status":       movie.status,
        "quality":      movie.quality,
        "lang":         movie.lang,
        "is_series":    movie.is_series,
        "chieurap":     movie.chieurap,
       
        "updated_at":   movie.updated_at.isoformat() if movie.updated_at else None,

        "episodes": [
            {
                "id":           str(ep.id),
                "name_episode": ep.name_episode,
                "slug":         ep.slug,
                "filename":     ep.filename,
                "link_embed":   ep.link_embed,
                "link_m3u8":    ep.link_m3u8,
                "server_name":  ep.server_name,
                "description":  ep.description,
            }
            for ep in movie.episodes
        ] if movie.episodes else []
    }


@celery_instance.task(name="tasks.sync_movie_to_es", queue="light_queue")
def sync_movie_to_es(movie_id: str):
    db = SessionLocal()
    try:
        movie = (db.query(MovieModel)
        .options(
            joinedload(MovieModel.actors),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.countries),
            joinedload(MovieModel.categories),
            joinedload(MovieModel.episodes)
            )
        .filter(
            MovieModel.id == movie_id,
            MovieModel.is_deleted == False
            )
        .first())

        if not movie:
            print(f"[ES Sync] Không tìm thấy phim {movie_id}")
            return

        doc = _build_movie_document(movie)
        es_client.index(index=MOVIE_INDEX, id=movie.id, document=doc)
        print(f"[ES Sync] Đã đồng bộ phim '{movie.name}' lên Elasticsearch")

    except Exception as e:
        print(f"[ES Sync] Lỗi: {e}")
    finally:
        db.close()

@celery_instance.task(name="tasks.bulk_sync_all_movies_to_es",queue="light_queue")
def task_bulk_sync_all_movies_to_es():
    db = SessionLocal()
    print("Đồng bộ hàng loạt bắt đầu")
    try:
        movies = (
            db.query(MovieModel)
            .filter(MovieModel.is_deleted == False)
            .options(
                subqueryload(MovieModel.actors),
                subqueryload(MovieModel.directors),
                subqueryload(MovieModel.categories),
                subqueryload(MovieModel.countries),
                subqueryload(MovieModel.episodes) 
            )
            .all()

        )

        if not movies:
            return "Không có dữ liệu phim để đồng bộ."

        actions = [
            {
                "_index": MOVIE_INDEX,
                "_id": str(movie.id),
                "_source": _build_movie_document(movie),
            }
            for movie in movies
        ]

        success, failed = bulk(es_client, actions)
        return f"Đồng bộ hàng loạt thành công: {success} phim, Thất bại: {len(failed)}"

    except Exception as e:
        print(f"[Bulk Sync ES] Lỗi: {e}")
        raise
    finally:
        db.close()

@celery_instance.task(name="tasks.delete_movie_from_es",queue="light_queue")
def delete_movie_from_es(movie_id: str):
    """Xóa 1 phim khỏi Elasticsearch. Gọi khi xóa phim hoặc set is_deleted."""
    try:
        es_client.delete(index=MOVIE_INDEX, id=movie_id, ignore=[404])
        print(f"[ES Sync] Đã xóa phim {movie_id} khỏi Elasticsearch")
    except Exception as e:
        print(f"[ES Sync] Lỗi xóa: {e}")