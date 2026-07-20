import httpx

from src.application.interfaces.external_services.movie_api_gateway_interface import IMovieApiGateway

import httpx

from src.application.interfaces.external_services.movie_api_gateway_interface import IMovieApiGateway


class MovieApiGateway(IMovieApiGateway):
    # Dùng riêng cho task sync — không đổi fetch_movies_list() cũ để tránh phá
    # chỗ khác đang gọi nó với hành vi "phim-moi-cap-nhat" mặc định.
    async def fetch_movies_list_paginated(self, list_type: str = "phim-le", page: int = 1):
        url = f"https://phimapi.com/danh-sach/{list_type}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params={"page": page})
            response.raise_for_status()
        return response.json()

    async def fetch_movies_list(self):
        print(" Vào được repo này")
        url = "https://phimapi.com/danh-sach/phim-moi-cap-nhat"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status() # báo lỗi
        return response.json()

    async def fetch_movie_detail_by_name(self, name: str):
        url = f"https://phimapi.com/phim/{name}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status() # báo lỗi
        return response.json()
    
    async def fetch_movie_detail_by_id(self, id: str):
        url = f"https://phimapi.com/tmdb/tv&movie/{id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status() # báo lỗi
        return response.json()

   
