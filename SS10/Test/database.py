from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy_utils import database_exists
DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/fastapi_db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush = False, autocommit = False )

def get_db ():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
Base = declarative_base()