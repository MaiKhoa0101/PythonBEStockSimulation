from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis as AsyncRedis  # ← đổi tên import

from src.presentation.controller.v1 import short
from src.presentation.controller.v1 import transaction
from src.presentation.controller.v1 import subscription, movies, users, collection
from src.infrastructure.database.session import Base, engine
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_client = AsyncRedis.from_url(redis_url, encoding="utf8", decode_responses=True)  

    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    print("Đã kết nối Redis thành công")
    yield
    await redis_client.close()
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

@app.get("/")
def root():
    return {"message": "Server is running! Access /docs for Swagger UI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)