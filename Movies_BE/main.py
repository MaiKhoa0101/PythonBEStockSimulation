from fastapi import FastAPI
from src.presentation.controller.v1 import movies,users,collection
from src.infrastructure.database.session import Base, engine
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)
app = FastAPI()

# Cấu hình CORS
origins = [
    "http://localhost:3000",      # Cho phép React/Vue Frontend (Web)
    "http://localhost:5173",      # Cho phép Vite
    "*"                           # Hoặc dùng "*" để cho phép tất cả (chỉ nên dùng khi dev)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Cho phép tất cả GET, POST, PUT, DELETE...
    allow_headers=["*"], # Cho phép gửi mọi loại Header (đặc biệt là header Authorization chứa Token)
)

# Gắn router vào ứng dụng chính
app.include_router(movies.router, prefix="/api/v1/movies")
app.include_router(users.router, prefix="/api/v1/users")
app.include_router(collection.router, prefix="/api/v1/collection")

@app.get("/")
def root():
    return {"message": "Server is running! Access /docs for Swagger UI"}

if __name__ == "__main__":
    import uvicorn
    # Lưu ý: "main:app" nghĩa là chạy biến 'app' ở trong file 'main.py'
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)