from fastapi import FastAPI
from src.presentation.controller.v1 import movies
from src.presentation.controller.v1 import users

app = FastAPI()


# Gắn router vào ứng dụng chính
app.include_router(movies.router, prefix="/api/v1/movies")
app.include_router(users.router, prefix="/api/v1/users")
@app.get("/")
def root():
    return {"message": "Server is running! Access /docs for Swagger UI"}

if __name__ == "__main__":
    import uvicorn
    # Lưu ý: "main:app" nghĩa là chạy biến 'app' ở trong file 'main.py'
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)