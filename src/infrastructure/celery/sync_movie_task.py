import asyncio
import os
from typing import List, Optional

import httpx

from src.infrastructure.services.movie.create_movie import CreateMovie
from src.infrastructure.celery.celery_app import celery_instance
from src.infrastructure.database.session import SessionLocal
from src.domain.entities.movies.movie import Episode, Movie
from src.presentation.dtos.movie_dto import EpisodeCreateDTO, MovieCreateDTO, MovieExternalIdsCreateDTO
from src.infrastructure.database.repositories.movie_repository import MoviesRepositories
from src.infrastructure.external_services.movie_api_gateway import MovieApiGateway
from src.infrastructure.database.utils.mapping import dto_to_entity

# ── Cấu hình qua env — theo đúng yêu cầu "quét từ trang n đến trang m" thay vì
# cố định 1 trang hay quét hết toàn bộ catalog mỗi 5 phút ───────────────────
SYNC_LIST_TYPE = os.getenv("SYNC_LIST_TYPE", "phim-le")
SYNC_PAGE_FROM = int(os.getenv("SYNC_PAGE_FROM", "1"))
SYNC_PAGE_TO = int(os.getenv("SYNC_PAGE_TO", "10"))
# Nghỉ nhẹ giữa các lần gọi /phim/{slug} để không dội API miễn phí của bên
# thứ 3 quá dồn dập trong 1 lần chạy (vài chục phim/trang).
SYNC_REQUEST_DELAY_SECONDS = float(os.getenv("SYNC_REQUEST_DELAY_SECONDS", "0.2"))


def _build_episode_dtos(episodes_raw: list) -> List[EpisodeCreateDTO]:
    """episodes_raw = detail["episodes"] dạng [{server_name, server_data: [...]}]."""
    dtos: List[EpisodeCreateDTO] = []
    for server in episodes_raw or []:
        server_name = server.get("server_name")
        for ep in server.get("server_data", []) or []:
            dtos.append(EpisodeCreateDTO(
                name_episode=ep.get("name") or "Full",
                slug=ep.get("slug"),
                filename=ep.get("filename"),
                link_embed=ep.get("link_embed"),
                link_m3u8=ep.get("link_m3u8"),
                server_name=server_name,
                description=None,
            ))
    return dtos


def _map_detail_to_create_dto(
    movie_obj: dict,
    episode_dtos: List[EpisodeCreateDTO],
    category_ids: List[str],
    country_ids: List[str],
) -> MovieCreateDTO:
    """Map response['movie'] của GET /phim/{slug} -> MovieCreateDTO.

    GIẢ ĐỊNH CẦN XÁC NHẬN LẠI VỚI RESPONSE THẬT (chưa có mẫu response đầy đủ
    của chính /phim/{slug} trong tay, chỉ suy theo format chuẩn họ ophim/kkphim):
    - movie_obj["content"]      -> mô tả phim (description)
    - movie_obj["category"]     -> [{"name":..., "slug":...}, ...]
    - movie_obj["country"]      -> [{"name":..., "slug":...}, ...]
    - movie_obj["tmdb"] / ["imdb"] -> giống hệt cấu trúc đã thấy ở list/search
    Nếu tên field thật khác, chỉ cần sửa trong hàm này, không ảnh hưởng chỗ khác.
    """
    tmdb = movie_obj.get("tmdb") or {}
    imdb = movie_obj.get("imdb") or {}

    external_ids: Optional[MovieExternalIdsCreateDTO] = None
    if tmdb.get("id") or imdb.get("id"):
        external_ids = MovieExternalIdsCreateDTO(
            tmdb_type=tmdb.get("type"),
            tmdb_id=tmdb.get("id"),
            tmdb_season=tmdb.get("season"),
            tmdb_vote_average=tmdb.get("vote_average"),
            tmdb_vote_count=tmdb.get("vote_count"),
            imdb_id=imdb.get("id"),
        )

    return MovieCreateDTO(
        name=movie_obj.get("name"),
        slug_name=movie_obj.get("slug"),
        origin_name=movie_obj.get("origin_name"),
        is_series=movie_obj.get("type") not in ("single", None),
        status="completed" if movie_obj.get("episode_current") == "Full" else "ongoing",
        description=movie_obj.get("content"),
        poster_url=movie_obj.get("poster_url"),
        thumb_url=movie_obj.get("thumb_url"),
        trailer_url=movie_obj.get("trailer_url"),
        quality=movie_obj.get("quality"),
        lang=movie_obj.get("lang"),
        time=movie_obj.get("time"),
        year=movie_obj.get("year"),
        episode_current=movie_obj.get("episode_current"),
        episode_total=str(movie_obj.get("episode_total")),
        is_copyright=bool(movie_obj.get("is_copyright", False)),
        sub_docquyen=bool(movie_obj.get("sub_docquyen", False)),
        chieurap=bool(movie_obj.get("chieurap", False)),
        episodes=episode_dtos,
        actor_ids=[],    # API nguồn không cung cấp actor/director
        director_ids=[],
        category_ids=category_ids,
        country_ids=country_ids,
        external_ids=external_ids,
    )


async def _sync_one_movie(gateway: MovieApiGateway, movie_repo: MoviesRepositories,
                           create_movie_service: CreateMovie, list_item: dict) -> None:
    slug = list_item.get("slug")
    if not slug:
        return
    print("Đang sync")
    try:
        detail = await gateway.fetch_movie_detail_by_name(slug)
    except httpx.HTTPStatusError as e:
        print(f"[SyncMovie] Lỗi HTTP khi lấy chi tiết '{slug}': {e}")
        return
    except httpx.HTTPError as e:
        print(f"[SyncMovie] Lỗi mạng khi lấy chi tiết '{slug}': {e}")
        return

    if not detail or detail.get("status") not in (True, "success"):
        print(f"[SyncMovie] Response không hợp lệ cho '{slug}', bỏ qua.")
        return

    movie_obj = detail.get("movie") or {}
    episode_dtos = _build_episode_dtos(detail.get("episodes"))

    existing_id = await movie_repo.find_movie_id_by_slug(slug)

    if existing_id:
        if not episode_dtos:
            return
        episode_entities = [
            dto_to_entity(ep, Episode, overrides={"id": "", "id_movie": ""})
            for ep in episode_dtos
        ]
        await movie_repo.upsert_episode(Movie(id=existing_id, episodes=episode_entities))
        print(f"[SyncMovie] '{slug}' đã tồn tại — đã kiểm tra/thêm {len(episode_entities)} episode.")
        return

    # Phim chưa có -> tạo mới, tự tạo category/country nếu DB chưa có (theo slug)
    category_ids = await movie_repo.get_or_create_categories(movie_obj.get("category") or [])
    country_ids = await movie_repo.get_or_create_countries(movie_obj.get("country") or [])

    movie_dto = _map_detail_to_create_dto(movie_obj, episode_dtos, category_ids, country_ids)
    created = await create_movie_service.create_movie(movie_dto)

    if created:
        print(f"[SyncMovie] Đã tạo phim mới: '{slug}' ({len(episode_dtos)} episode).")
    else:
        print(f"[SyncMovie] Tạo phim '{slug}' thất bại (create_movie trả None).")


async def _run_sync() -> None:
    db = SessionLocal()
    try:
        movie_repo = MoviesRepositories(db)
        create_movie_service = CreateMovie(movie_repo)
        gateway = MovieApiGateway()

        for page in range(SYNC_PAGE_FROM, SYNC_PAGE_TO + 1):
            try:
                list_data = await gateway.fetch_movies_list_paginated(SYNC_LIST_TYPE, page)
                
            except httpx.HTTPError as e:
                print(f"[SyncMovie] Lỗi khi lấy trang {page}: {e}")
                continue

            items = list_data.get("items") or []
            print(f"[SyncMovie] Trang {page}: {len(items)} phim.")

            for item in items:
                await _sync_one_movie(gateway, movie_repo, create_movie_service, item)
                if SYNC_REQUEST_DELAY_SECONDS > 0:
                    await asyncio.sleep(SYNC_REQUEST_DELAY_SECONDS)

    except Exception as e:
        db.rollback()
        print(f"[SyncMovie] Lỗi không mong muốn, rollback: {e}")
    finally:
        db.close()


YEAR_START = 2020
YEAR_END = 2026
async def _run_sync_by_year() -> None:
    db = SessionLocal()
    try:
        movie_repo = MoviesRepositories(db)
        create_movie_service = CreateMovie(movie_repo)
        gateway = MovieApiGateway()

        for year in range(YEAR_START, YEAR_END + 1):

            try:
                first_page = await gateway.fetch_movies_list_paginated_by_year(
                    page=1,
                    year=year
                )
            except httpx.HTTPError as e:
                print(f"[SyncMovie] Không lấy được dữ liệu năm {year}: {e}")
                continue

            pagination = (
                first_page.get("data", {})
                          .get("params", {})
                          .get("pagination", {})
            )

            total_pages = pagination.get("totalPages", 1)

            print(f"Năm {year}: {total_pages} trang")

            # xử lý luôn trang đầu
            items = first_page.get("data", {}).get("items", [])
            for item in items:
                await _sync_one_movie(
                    gateway,
                    movie_repo,
                    create_movie_service,
                    item,
                )

                if SYNC_REQUEST_DELAY_SECONDS:
                    await asyncio.sleep(SYNC_REQUEST_DELAY_SECONDS)

            # các trang còn lại
            for page in range(2, total_pages + 1):

                try:
                    page_data = await gateway.fetch_movies_list_paginated_by_year(
                        page=page,
                        year=year
                    )
                except httpx.HTTPError as e:
                    print(f"[SyncMovie] Lỗi năm {year} trang {page}: {e}")
                    continue

                items = page_data.get("data", {}).get("items", [])

                print(f"Năm {year} - Trang {page}: {len(items)} phim")

                for item in items:
                    await _sync_one_movie(
                        gateway,
                        movie_repo,
                        create_movie_service,
                        item,
                    )

                    if SYNC_REQUEST_DELAY_SECONDS:
                        await asyncio.sleep(SYNC_REQUEST_DELAY_SECONDS)

    except Exception as e:
        db.rollback()
        print(f"[SyncMovie] Lỗi không mong muốn: {e}")

    finally:
        db.close()

@celery_instance.task(name="tasks.sync_movies_from_external", queue="heavy_queue")
def sync_movies_from_external():
    """Celery task LÀ hàm sync (không async) — bọc asyncio.run() để gọi được
    xuống các lớp service/repository/gateway vốn viết async def (theo đúng
    cách celery_app.py đã include các task khác, xem sync_movie_to_es làm mẫu:
    `db = SessionLocal(); ... finally: db.close()`)."""
    asyncio.run(_run_sync_by_year())