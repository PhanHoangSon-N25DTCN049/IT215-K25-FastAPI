from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker , DeclarativeBase

DATABASE_URL = "sqlite:///./ev_charging_db.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit = False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
class Base(DeclarativeBase):
    pass
