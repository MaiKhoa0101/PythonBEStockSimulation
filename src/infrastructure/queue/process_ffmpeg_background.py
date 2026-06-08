import os
import asyncio
import ffmpeg
from src.infrastructure.database.repositories.movie_repository import MoviesRepositories
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.queue.celery_app import celery_instance
@celery_instance.task(name="tasks.process_ffmpeg_video")
def process_ffmpeg_video_task(temp_path: str, target_dir: str, episode_id: str, relative_db_path: str, is_short: bool):
    try:
        m3u8_full_path = os.path.join(target_dir, "index.m3u8")
        print(f"🎬 [CELERY WORKER] Đang băm HLS tại: {m3u8_full_path}")
        
        ffmpeg.input(temp_path).output(
            m3u8_full_path, 
            format='hls', 
            hls_time=10, 
            hls_list_size=0, 
            c='copy'
        ).run(
            overwrite_output=True, 
            capture_stdout=True, 
            capture_stderr=True
        )

        # 🔥 LƯU Ý 2: Vì hàm `upload_episode` của Repo là ASYNC, nhưng Celery chạy SYNC,
        # ta sẽ bọc logic cập nhật DB vào một hàm async cục bộ và chạy bằng asyncio.run()
        if not is_short:
            async def update_database():
                db_session = SessionLocal() # Tự mở session mới cho Worker
                try:
                    # Khởi tạo Repo thủ công bằng session vừa tạo
                    movie_repository = MoviesRepositories(db_session) 
                    is_updated = await movie_repository.upload_episode(
                        episode_id, relative_db_path, is_hls=True  
                    )
                    if not is_updated:
                        print(f"❌ [CELERY WORKER] Không tìm thấy tập {episode_id} để cập nhật DB.")
                finally:
                    await db_session.close() # Dùng xong phải đóng ngay tránh leak connection

            # Kích hoạt chạy hàm async trong môi trường sync của Celery
            asyncio.run(update_database())

    except Exception as e:
        print(f"❌ [CELERY WORKER] Lỗi quá trình xử lý HLS: {str(e)}")
    finally:
        # Xóa file gốc tạm thời sau khi băm xong
        if os.path.exists(temp_path):
            os.remove(temp_path)