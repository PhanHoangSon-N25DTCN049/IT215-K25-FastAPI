from fastapi import FastAPI, Depends, HTTPException
from app.models import *
from app.db import Base, engine, get_db
from sqlalchemy.orm import Session
from app.core import setup_exception_handlers
from app.routers import api_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

setup_exception_handlers(app)

app.include_router(api_router)


@app.get("/")
def get_heal(db: Session = Depends(get_db)):
    try:
        db.connection()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="lỗi server"
        )
    return {
        "message": "Kết nối database Thành công"
    } 