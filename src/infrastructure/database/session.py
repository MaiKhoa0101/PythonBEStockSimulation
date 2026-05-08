 # Cấu hình kết nối DB
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv


load_dotenv()
#lấy url kết nối từ biến môi trường
SQLALCHEMY_DATABASE_URL= os.getenv("SQLALCHEMY_DATABASE_URL")
# Khởi tạo engine, echo laf in ra câu lệnh SQL để debug,
# bind là kết nối engine với session
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True) 


# Autocommit=False: mỗi lần thực hiện xong 1 câu lệnh 
# SQL sẽ không tự động commit
# Phải gọi lệnh db.commit() thì tất cả mới được lưu 
# cùng lúc. Nếu gặp lỗi thì có thể gọi db.rollback() để hủy toàn bộ.

# Autoflush=False: sau khi thực hiện xong 1 
# câu lệnh SQL thì session sẽ không tự động 
# flush dữ liệu xuống database
# mà sẽ đợi đến khi nào gọi lệnh 
# db.flush() hoặc db.commit() thì mới 
# flush dữ liệu xuống database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Bản gốc
Base = declarative_base()

# Hàm để lấy database session, 
# dùng trong dependency injection của FastAPI
def get_db():
    db = SessionLocal() # 1. Mở một phiên làm việc mới
    try:
        yield db        # 2. Tạm dừng ở đây, ném db cho API dùng
    finally:
        db.close()      # 3. Khi API chạy xong, CHẮC CHẮN sẽ đóng kết nối