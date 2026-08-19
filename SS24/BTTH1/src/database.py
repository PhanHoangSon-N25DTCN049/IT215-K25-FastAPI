from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# connect_args={"check_same_thread": False} cần thiết khi dùng SQLite với FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency cung cấp db session cho mỗi request và tự động đóng sau khi hoàn tất."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
