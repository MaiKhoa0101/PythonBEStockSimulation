import httpx

from src.application.interfaces.external_services.movie_apu_gateway_interface import IMovieApiGateway


class MovieApiGateway(IMovieApiGateway):
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

   
