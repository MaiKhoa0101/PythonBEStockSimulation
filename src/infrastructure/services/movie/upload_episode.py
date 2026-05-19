import asyncio
import os

import aiofiles
from fastapi import BackgroundTasks, HTTPException, UploadFile
import ffmpeg

from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import IUploadEpisode

class UploadEpisode(IUploadEpisode):
    def __init__(self, movie_repository: IMoviesRepository):
        self.movie_repository = movie_repository

    async def upload_episode_video_into_local_system_path(
        self, movie_slug: str, episode_id: str, file: UploadFile
    ) -> str:
        file_ext = self._validate_and_get_extension(file.filename)

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        target_dir = os.path.join(base_dir, "media", "movies", movie_slug, episode_id)
        os.makedirs(target_dir, exist_ok=True)

        file_name = f"video{file_ext}"
        full_path = os.path.join(target_dir, file_name)
        relative_db_path = f"movies/{movie_slug}/{episode_id}/{file_name}"

        await self._write_upload_file(file, full_path)

        try:
            is_updated = await self.movie_repository.upload_episode(episode_id, relative_db_path)
            if not is_updated:
                raise Exception("Không tìm thấy Tập phim trong hệ thống")
            return relative_db_path
        except Exception as e:
            if os.path.exists(full_path):
                os.remove(full_path)
            raise HTTPException(status_code=500, detail=str(e))

    async def upload_episode_video_hls(
        self, movie_slug: str, episode_id: str, file: UploadFile, bg_tasks: BackgroundTasks
    ) -> str:
        file_ext = self._validate_and_get_extension(file.filename)  

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

        temp_dir = os.path.join(base_dir, "media", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{episode_id}_goc{file_ext}")

        target_dir = os.path.join(base_dir, "media", "movies", movie_slug, episode_id)
        os.makedirs(target_dir, exist_ok=True)

        relative_db_path = f"movies/{movie_slug}/{episode_id}/index.m3u8"

        await self._write_upload_file(file, temp_path) 

        bg_tasks.add_task(
            self._process_ffmpeg_background,
            temp_path=temp_path,
            target_dir=target_dir,
            episode_id=episode_id,
            relative_db_path=relative_db_path,
        )

        return relative_db_path


    async def _process_ffmpeg_background(
        self, temp_path: str, target_dir: str, episode_id: str, relative_db_path: str
    ):
        try:
            m3u8_full_path = os.path.join(target_dir, "index.m3u8")

            def run_ffmpeg():
                (
                    ffmpeg
                    .input(temp_path)
                    .output(
                        m3u8_full_path, 
                        format='hls', 
                        hls_time=10,
                        hls_list_size=0, 
                        c='copy'
                    )
                    .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
                )

            await asyncio.to_thread(run_ffmpeg)

            is_updated = await self.movie_repository.upload_episode(episode_id, relative_db_path)
            if not is_updated:
                print(f"Cảnh báo: Không tìm thấy tập {episode_id} để cập nhật DB.")

        except Exception as e:
            print(f"Lỗi quá trình xử lý HLS: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    
    def _validate_and_get_extension(self, filename: str) -> str:
        """Validate file extension, trả về ext (vd: '.mp4') hoặc raise 400."""
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in {'.mp4', '.mkv', '.avi'}:
            raise HTTPException(status_code=400, detail="Định dạng không hỗ trợ")
        return file_ext

    async def _write_upload_file(self, file: UploadFile, full_path: str) -> None:
        """Ghi raw bytes từ UploadFile xuống full_path, đóng file sau khi xong."""
        try:
            async with aiofiles.open(full_path, 'wb') as out_file:
                while chunk := await file.read(1024 * 1024):
                    await out_file.write(chunk)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi ghi file: {str(e)}")
        finally:
            await file.close()