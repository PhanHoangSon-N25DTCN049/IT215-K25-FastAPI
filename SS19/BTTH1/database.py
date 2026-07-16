from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/supply_chain_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Định nghĩa Base class theo phong cách SQLAlchemy 2.0
class Base(DeclarativeBase):
    pass

# Dependency quản lý session an toàn
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()