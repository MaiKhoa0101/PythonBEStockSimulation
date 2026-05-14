from typing import Protocol


class IVideoHandler (Protocol):
    async def download_video_from_url(self, video_path: str):
        ...
    async def download_video_from_upload(self, video_path: str):
        ...