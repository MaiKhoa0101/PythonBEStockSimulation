from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.presentation.controller.v1 import short
from src.presentation.controller.v1 import transaction
from src.presentation.controller.v1 import subscription, movies,users,collection
from src.infrastructure.database.session import Base, engine
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)
app = FastAPI()

# Cấu hình CORS
origins = [
    "*"
]

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⏳ Đang kết nối tới Máy chủ Redis...")
    # Kết nối tới con Docker Redis đang chạy ở cổng 6379
    redis = aioredis.from_url("redis://localhost:6379", encoding="utf8", decode_responses=True)
    
    # Kích hoạt Cache cho toàn bộ FastAPI
    FastAPICache.init(RedisBackend(redis), prefix="app-cache")
    print("✅ Đã kết nối Redis thành công! App sẵn sàng.")
    
    yield # Cho phép FastAPI chạy...
    
    # Khi bạn tắt server (Ctrl+C), nó sẽ ngắt kết nối an toàn
    await redis.close()
    print("🛑 Đã ngắt kết nối Redis.")

@app.get("/")
def root():
    return {"message": "Server is running! Access /docs for Swagger UI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)