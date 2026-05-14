

import asyncio
import os

import aiofiles
import httpx

from src.infrastructure.utils.video_handler import _base_url


async def _download_hls(m3u8_url: str, folder: str) -> str:
    """
    Tải HLS stream (.m3u8) về local, ghép thành 1 file .mp4 bằng ffmpeg.
 
    Luồng xử lý:
        1. Tải file .m3u8  → parse danh sách segment .ts
        2. Tải song song tất cả segment .ts (semaphore 10)
        3. Ghi danh sách segment ra file concat list
        4. Gọi ffmpeg ghép thành output.mp4
        5. Dọn dẹp file .ts và concat list
 
    Returns:
        Đường dẫn file .mp4 đã ghép
    """
    base = _base_url(m3u8_url)
    output_path = os.path.join(folder, "output.mp4")
 
    # --- Bước 1: Tải và parse .m3u8 ---
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        resp = await client.get(m3u8_url)
        if resp.status_code != 200:
            raise ValueError(f"Không tải được .m3u8. Status: {resp.status_code}")
        m3u8_content = resp.text
 
    # Lọc ra các dòng segment (không bắt đầu bằng #, không rỗng)
    segments = [
        line.strip()
        for line in m3u8_content.splitlines()
        if line.strip() and not line.startswith("#")
    ]
 
    if not segments:
        raise ValueError("File .m3u8 không chứa segment nào.")
 
    # Resolve URL tương đối
    segment_urls = [
        seg if seg.startswith("http") else base + seg
        for seg in segments
    ]
 
    print(f"[HLS] Tìm thấy {len(segment_urls)} segments, bắt đầu tải...")
 
    # --- Bước 2: Tải song song các segment .ts ---
    segment_paths: list[str | None] = [None] * len(segment_urls)
 
    async def _fetch_segment(idx: int, seg_url: str):
        seg_path = os.path.join(folder, f"seg_{idx:05d}.ts")
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            async with client.stream("GET", seg_url) as r:
                if r.status_code != 200:
                    raise IOError(f"Tải segment {idx} thất bại. Status: {r.status_code}")
                async with aiofiles.open(seg_path, "wb") as f:
                    async for chunk in r.aiter_bytes(CHUNK_SIZE):
                        await f.write(chunk)
        segment_paths[idx] = seg_path
 
    # Giới hạn concurrency: tải tối đa 10 segment cùng lúc
    semaphore = asyncio.Semaphore(10)
 
    async def _fetch_with_sem(idx: int, seg_url: str):
        async with semaphore:
            await _fetch_segment(idx, seg_url)
 
    await asyncio.gather(*[
        _fetch_with_sem(i, url) for i, url in enumerate(segment_urls)
    ])
 
    print(f"[HLS] Tải xong {len(segment_urls)} segments, bắt đầu ghép...")
 
    # --- Bước 3: Ghi concat list cho ffmpeg ---
    concat_path = os.path.join(folder, "concat.txt")
    async with aiofiles.open(concat_path, "w") as f:
        for seg_path in segment_paths:
            await f.write(f"file '{os.path.abspath(seg_path)}'\n")
 
    # --- Bước 4: Ghép bằng ffmpeg (không re-encode → rất nhanh) ---
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_path,
        "-c", "copy",
        output_path
    ]
 
    proc = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
 
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg thất bại:\n{stderr.decode(errors='ignore')}")
 
    # --- Bước 5: Dọn dẹp file tạm ---
    for seg_path in segment_paths:
        if seg_path and os.path.exists(seg_path):
            os.remove(seg_path)
    if os.path.exists(concat_path):
        os.remove(concat_path)
 
    print(f"[HLS] Ghép xong → {output_path}")
    return output_path
 


