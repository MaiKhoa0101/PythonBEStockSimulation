from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis as AsyncRedis

from src.presentation.controller.v1 import log_controller
from src.infrastructure.elasticsearch.es_client import create_movie_index
from src.presentation.controller.v1 import short
from src.presentation.controller.v1 import transaction
from src.presentation.controller.v1 import subscription, movies, users, collection
from src.infrastructure.database.session import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from src.infrastructure.database.redis import redis_pool

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(RedisBackend(redis_pool), prefix="fastapi-cache")
    print("Đã kết nối Redis thành công")
    create_movie_index()
    yield
    await redis_pool.close()
    print("Đã ngắt kết nối Redis.")

app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(movies.router, prefix="/api/v1/movies")
app.include_router(movies.router, prefix="/api/v2/movies")
app.include_router(users.router, prefix="/api/v1/users")
app.include_router(collection.router, prefix="/api/v1/collection")
app.include_router(subscription.router, prefix="/api/v1/subscription")
app.include_router(transaction.router, prefix="/api/v1/transaction")
app.include_router(short.router, prefix="/api/v1/shorts")
app.include_router(log_controller.router, prefix="/api/v1/logs", tags=["Logs"])

@app.get("/")
def root():
    return {"message": "Server is running! Access /docs for Swagger UI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)