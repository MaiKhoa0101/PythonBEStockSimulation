from typing import Optional

from slugify import slugify

from src.application.interfaces.external_services.movie_api_gateway_interface import IMovieApiGateway
from src.application.interfaces.services.movies_service_interface import IGetListMoviesService
from src.application.interfaces.repositories.movie_repository_interface import IMoviesRepository


class GetListMovies(IGetListMoviesService):
    def __init__(
            self, 
            movie_repository: IMoviesRepository, 
            movie_external_service: IMovieApiGateway
        ):
        self.movie_repository = movie_repository
        self.movie_external_service = movie_external_service

    async def fetch_movies_list(
        self,
        page: int = 1,
        size: int = 30,
        q: Optional[str] = None,
        category_id: Optional[str] = None,
        country_slug: Optional[str] = None,
        status: Optional[str] = None,
        is_series: Optional[bool] = None,
        quality: Optional[str] = None,
        year: Optional[int] = None,
    ):
        print(" Vào được đây")
        data = await self.movie_repository.fetch_movies_list(
            page=page,
            size=size,
            q=q,
            category_id=category_id,
            country_slug=country_slug,
            status=status,
            is_series=is_series,
            quality=quality,
            year=year,
        )

        no_filter_applied = not any([
            q, category_id, country_slug, status, is_series is not None, quality, year is not None
        ])
        if (not data or not data.get("results")) and no_filter_applied:
            data = await self.movie_external_service.fetch_movies_list()
            if not data:
                return None
        return data