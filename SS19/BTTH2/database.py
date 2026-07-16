from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Thay đổi cấu hình user/password phù hợp với MySQL của bạn
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/healthcare_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()