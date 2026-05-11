from sqlalchemy import Table, Column, String, ForeignKey
from src.infrastructure.database.session import Base

movie_category_association = Table(
    "movie_category",
    Base.metadata,
    Column("id_movie", String(50), ForeignKey("movie.id"), primary_key=True),
    Column("id_category", String(50), ForeignKey("category.id"), primary_key=True),
)

movie_actor_association = Table(
    "movie_actor",
    Base.metadata,
    Column("id_movie", String(50), ForeignKey("movie.id"), primary_key=True),
    Column("id_actor", String(50), ForeignKey("actor.id"), primary_key=True),
)

movie_director_association = Table(
    "movie_director",
    Base.metadata,
    Column("id_movie", String(50), ForeignKey("movie.id"), primary_key=True),
    Column("id_director", String(50), ForeignKey("director.id"), primary_key=True),
)


movie_country_association = Table(
    "movie_country",
    Base.metadata,
    Column("id_movie", String(50), ForeignKey("movie.id"), primary_key=True),
    Column("id_country", String(50), ForeignKey("country.id"), primary_key=True),
)
