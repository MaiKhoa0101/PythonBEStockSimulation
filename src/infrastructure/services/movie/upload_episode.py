import asyncio
import os
import uuid

import aiofiles
from fastapi import BackgroundTasks, HTTPException, UploadFile
import ffmpeg

from src.infrastructure.celery.hls_task import process_hls_task
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import IUploadEpisode

class UploadEpisode(IUploadEpisode):
    def __init__(self, movie_repository: IMoviesRepository):
        self.movie_repository = movie_repository

    def _get_base_dir(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

    def _validate_and_get_extension(self, filename: str) -> str:
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in {'.mp4', '.mkv', '.avi'}:
            raise HTTPException(status_code=400, detail="Định dạng không hỗ trợ")
        return file_ext

    async def _write_upload_file(self, file: UploadFile, full_path: str) -> None:
        try:
            async with aiofiles.open(full_path, 'wb') as out_file:
                while chunk := await file.read(1024 * 1024):
                    await out_file.write(chunk)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi ghi file: {str(e)}")
        finally:
            await file.close()

    async def upload_episode_video_into_local_system_path(
        self, movie_slug: str, episode_slug: str, episode_id: str, file: UploadFile
    ) -> str:
        file_ext = self._validate_and_get_extension(file.filename)

        # media/movie/{movie_slug}/{episode_slug}/full-ep/
        target_dir = os.path.join(self._get_base_dir(), "media", "movie", movie_slug, episode_slug, "full-ep")
        os.makedirs(target_dir, exist_ok=True)

        file_name = f"video{file_ext}"
        full_path = os.path.join(target_dir, file_name)
        relative_db_path = f"media/movie/{movie_slug}/{episode_slug}/full-ep/{file_name}"

        await self._write_upload_file(file, full_path)

        try:
            is_updated = await self.movie_repository.upload_episode(
                episode_id, relative_db_path, is_hls=False   # → link_embed
            )
            if not is_updated:
                raise Exception("Không tìm thấy Tập phim trong hệ thống")
            return relative_db_path
        except Exception as e:
            if os.path.exists(full_path):
                os.remove(full_path)
            raise HTTPException(status_code=500, detail=str(e))

    async def upload_episode_video_hls(
        self, first_folder: str, episode_slug: str, file: UploadFile, bg_tasks: BackgroundTasks, is_short: bool = False
    ) -> str:
        file_ext = self._validate_and_get_extension(file.filename)
        base_dir = self._get_base_dir()

        random_id = uuid.uuid4().hex[:8]

        temp_dir = os.path.join(base_dir, "media", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{episode_slug}_goc{file_ext}")

        if not is_short:
            target_dir = os.path.join(base_dir, "media", "movie", first_folder, episode_slug, "hls", random_id)
            relative_db_path = f"media/movie/{first_folder}/{episode_slug}/hls/{random_id}/index.m3u8"
        else:
            target_dir = os.path.join(base_dir, "media", "short", first_folder, episode_slug, "hls", random_id)
            relative_db_path = f"media/short/{first_folder}/{episode_slug}/hls/{random_id}/index.m3u8"

        os.makedirs(target_dir, exist_ok=True)

        await self._write_upload_file(file, temp_path)
        print("Xu ly upload hls")


        # bg_tasks.add_task(
        #     self._process_ffmpeg_background,
        #     temp_path=temp_path,
        #     target_dir=target_dir,
        #     episode_id=episode_slug,
        #     relative_db_path=relative_db_path,
        #     is_short=is_short
        # )
        process_hls_task.delay(
            temp_path=temp_path,
            target_dir=target_dir,
            episode_id=episode_slug,
            relative_db_path=relative_db_path,
            is_short=is_short,
        )
        print(f"[UploadEpisode] Đã đẩy task HLS vào Celery queue: {relative_db_path}")
        return relative_db_path
    
    async def _process_ffmpeg_background(
        self, temp_path: str, target_dir: str, episode_id: str, relative_db_path: str,is_short
    ):
        try:
            m3u8_full_path = os.path.join(target_dir, "index.m3u8")
            print ("Xu ly upload hls voi path "+m3u8_full_path)

            await asyncio.to_thread(                    
                    ffmpeg
                    .input(temp_path)
                    .output(
                        m3u8_full_path, 
                        format='hls', 
                        hls_time=10, 
                        hls_list_size=0, 
                        c='copy'
                    )
                    .run(
                        overwrite_output=True, 
                        capture_stdout=True, 
                        capture_stderr=True
                    )
            )
            if not is_short:
                is_updated = await self.movie_repository.upload_episode(
                    episode_id, relative_db_path, is_hls=True  
                )
                if not is_updated:
                    print(f"Cảnh báo: Không tìm thấy tập {episode_id} để cập nhật DB.")

        except Exception as e:
            print(f"Lỗi quá trình xử lý HLS: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)