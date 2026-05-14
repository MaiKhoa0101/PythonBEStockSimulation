import os

import aiofiles
from fastapi import HTTPException, UploadFile

from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository
from src.application.interfaces.services.movies_service_interface import IUploadEpisode


class UploadEpisode (IUploadEpisode):
    def __init__(
        self, 
        movie_repository: IMoviesRepository
    ):
        self.movie_repository = movie_repository



    async def upload_episode_video(self, movie_slug: str, episode_id: str, file: UploadFile) -> str:       
        #Check đuôi file
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.mp4', '.mkv', '.avi']:
            raise HTTPException(status_code=400, detail="Định dạng không hỗ trợ")

        #Set đường dẫn
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        target_dir = os.path.join(base_dir, "media", "movies", movie_slug, episode_id)
        os.makedirs(target_dir, exist_ok=True)

        file_name = f"video{file_ext}"
        full_path = os.path.join(target_dir, file_name)
        relative_db_path = f"movies/{movie_slug}/{episode_id}/{file_name}"

        try:
            async with aiofiles.open(full_path, 'wb') as out_file:
                while content := await file.read(1024 * 1024):
                    await out_file.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi ghi file vật lý: {str(e)}")
        finally:
            await file.close()

        try:
            is_updated = await self.movie_repository.upload_episode(episode_id, relative_db_path)
            if not is_updated:
                raise Exception("Không tìm thấy Tập phim trong hệ thống")
            
            return relative_db_path
            
        except Exception as e:
            if os.path.exists(full_path):
                os.remove(full_path)
            raise HTTPException(status_code=500, detail=str(e))