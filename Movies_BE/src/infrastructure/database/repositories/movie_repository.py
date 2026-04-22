import httpx
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository


class MoviesRepositories(IMoviesRepository):
    
    async def fetch_movies_list(self):
        print(" Vào được repo này")
        url = "https://phimapi.com/danh-sach/phim-moi-cap-nhat"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status() # báo lỗi
        #return {"message": "Test thanh cong"}