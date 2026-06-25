
from src.infrastructure.elasticsearch.es_client import es_client, MOVIE_INDEX
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.models.movies.movie_model import MovieModel
from src.infrastructure.celery.celery_app import celery_instance
from elasticsearch.helpers import bulk
from sqlalchemy.orm import subqueryload

def _build_movie_document(movie: MovieModel) -> dict:
    return {
        "id":           movie.id,
        "name":         movie.name,
        "origin_name":  movie.origin_name,
        "description":  movie.description,
        "actors":       [actor.name for actor in movie.actors],
        "directors":    [director.name for director in movie.directors],
        "categories":   [cat.name for cat in movie.categories], 
        "countries":    [c.slug for c in movie.countries],     
        "slug_name":    movie.slug_name,
        "poster_url":   movie.poster_url,
        "thumb_url":    movie.thumb_url,
        "year":         movie.year,
        "view":         movie.view,
        "is_deleted":   movie.is_deleted,
        "status":       movie.status,    
        "quality":      movie.quality,   
        "lang":         movie.lang,       
        "is_series":    movie.is_series,   
        "chieurap":     movie.chieurap, 
    }

@celery_instance.task(name="tasks.sync_movie_to_es", queue="light_queue")
def sync_movie_to_es(movie_id: str):
    db = SessionLocal()
    try:
        movie = db.query(MovieModel).filter(MovieModel.id == movie_id).first()

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

        actions = []
        for movie in movies:
            episodes_data = [
                {
                    "id":           str(ep.id),
                    "name_episode": ep.name_episode,
                    "slug":         ep.slug,
                    "filename":     ep.filename,
                    "link_embed":   ep.link_embed,
                    "link_m3u8":    ep.link_m3u8,
                    "server_name":  ep.server_name,
                    "description":  ep.description
                }
                for ep in movie.episodes
            ]

            doc = {
                "_index": MOVIE_INDEX,
                "_id": str(movie.id),
                "_source": {
                    "id":           str(movie.id),
                    "name":         movie.name,
                    "origin_name":  movie.origin_name,
                    "description":  movie.description,
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
                    
                    "actors":       [a.name for a in movie.actors],      
                    "directors":    [d.name for d in movie.directors],
                    "categories":   [c.name for c in movie.categories],
                    "countries":    [co.name for co in movie.countries],
                    
                    "episodes":     episodes_data
                }
            }
            actions.append(doc)

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