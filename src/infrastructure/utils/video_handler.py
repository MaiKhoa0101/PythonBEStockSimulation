import asyncio
import os
from typing import Protocol
from urllib.parse import urlparse
import uuid

import aiofiles
from fastapi import UploadFile
import httpx
from src.infrastructure.utils.download_hls_video import _download_hls
from src.application.interfaces.utils.video_handler import IVideoHandler


MEDIA_ROOT = os.getenv("MEDIA_ROOT")
MAX_UPLOAD_SIZE = os.getenv("MAX_UPLOAD_SIZE")
CHUNK_SIZE = os.getenv("CHUNK_SIZE") 
ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS")

def _build_folder(slug_movie: str, slug_episode: str) -> str:
    """
    Tạo và trả về path thư mục: media/movie/<slug_movie>/<slug_episode>
    """
    folder = os.path.join(MEDIA_ROOT, slug_movie, slug_episode)
    os.makedirs(folder, exist_ok=True)
    return folder

def _is_m3u8(url: str) -> bool:
    path = urlparse(url).path
    return path.lower().endswith(".m3u8")

def _safe_filename(original: str) -> str:
    _, ext = os.path.splitext(original)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".mp4"  # fallback
    return f"{uuid.uuid4().hex}{ext}"

def _base_url(m3u8_url: str) -> str:
    """
    Lấy base URL để resolve các segment URL tương đối trong file .m3u8.
    VD: https://cdn.com/20250605/abc/index.m3u8 → https://cdn.com/20250605/abc/
    """
    return m3u8_url.rsplit("/", 1)[0] + "/"


 
async def _download_direct(video_url: str, folder: str) -> str:
    """
    Tải file video thông thường (mp4, mkv, ...) bằng HTTP streaming.
    """
    raw_name = video_url.split("?")[0].split("/")[-1] or "video.mp4"
    _, ext = os.path.splitext(raw_name)
    ext = ext.lower() if ext.lower() in ALLOWED_EXTENSIONS else ".mp4"
    save_path = os.path.join(folder, f"{uuid.uuid4().hex}{ext}")
 
    async with httpx.AsyncClient(timeout=600, follow_redirects=True) as client:
        async with client.stream("GET", video_url) as response:
            if response.status_code != 200:
                raise ValueError(f"Tải video thất bại. Status: {response.status_code}")
            async with aiofiles.open(save_path, "wb") as f:
                async for chunk in response.aiter_bytes(CHUNK_SIZE):
                    await f.write(chunk)
 
    return save_path
 

 
class VideoHandler(IVideoHandler):
 
    async def download_video_from_url(
        self,
        video_url: str,
        slug_movie: str,
        slug_episode: str,
    ) -> str:
        """
        Tải video từ URL về local.
        Hỗ trợ 3 dạng URL:
          - Player wrapper : https://player.phimapi.com/player/?url=<real_url>
          - HLS stream     : https://cdn.com/.../index.m3u8
          - Direct video   : https://cdn.com/.../video.mp4
 
        Lưu vào: media/movie/<slug_movie>/<slug_episode>/output.mp4
 
        Returns:
            Path local của file đã lưu.
        """
        if not video_url:
            raise ValueError("video_url không được để trống.")
 
        # Unwrap nếu là player URL
        print(f"[VideoHandler] Real URL: {video_url}")
 
        folder = _build_folder(slug_movie, slug_episode)
 
        if _is_m3u8(video_url):
            return await _download_hls(video_url, folder)
        else:
            return await _download_direct(video_url, folder)
 
    async def download_video_from_upload(
        self,
        upload_file: UploadFile,
        slug_movie: str,
        slug_episode: str,
    ) -> str:
        """
        Nhận file upload từ client và lưu vào:
        media/movie/<slug_movie>/<slug_episode>/<uuid>.<ext>
 
        Returns:
            Path local của file đã lưu.
        """
        if not upload_file.filename:
            raise ValueError("File upload không có tên.")
 
        _, ext = os.path.splitext(upload_file.filename)
        ext = ext.lower() if ext.lower() in ALLOWED_EXTENSIONS else ".mp4"
 
        folder = _build_folder(slug_movie, slug_episode)
        save_path = os.path.join(folder, f"{uuid.uuid4().hex}{ext}")
 
        total_written = 0
        async with aiofiles.open(save_path, "wb") as f:
            while True:
                chunk = await upload_file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_written += len(chunk)
                if total_written > MAX_UPLOAD_SIZE:
                    await f.close()
                    os.remove(save_path)
                    raise ValueError("File vượt quá giới hạn 2GB.")
                await f.write(chunk)
 
        if total_written == 0:
            os.remove(save_path)
            raise ValueError("File upload rỗng.")
 
        return save_path
 
