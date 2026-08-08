from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./ngay5.db"


engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush= False, autocommit = False)

def get_db():
    db = SessionLocal()    
    try:
        yield db
    finally:
        db.close()