from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Đường dẫn kết nối đến cơ sở dữ liệu MySQL (Thay đổi user, password, db_name phù hợp)

DATABASE_URL = "sqlite:///./db.db"

# Tạo bộ máy kết nối (Engine)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
# Tạo lớp session để giao tiếp với DB

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Lớp cơ sở để định nghĩa các Model thực thể
Base = declarative_base()
# Dependency cung cấp Session cho từng Request và tự động đóng lại khi hoàn thành

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
