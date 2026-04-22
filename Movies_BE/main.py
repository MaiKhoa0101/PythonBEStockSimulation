from fastapi import FastAPI
from src.presentation.controller.v1 import get_movie_list

app = FastAPI(
    title="Movies Backend API",
    version="1.0.0"
)

# Gắn router vào ứng dụng chính
app.include_router(get_movie_list.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Server is running! Access /docs for Swagger UI"}

if __name__ == "__main__":
    import uvicorn
    # Lưu ý: "main:app" nghĩa là chạy biến 'app' ở trong file 'main.py'
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)