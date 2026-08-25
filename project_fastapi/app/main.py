from fastapi import FastAPI, Depends, HTTPException, status
from app.models import *
from app.db import Base, engine, get_db
from sqlalchemy.orm import Session
from app.core import setup_exception_handlers, settings
from app.routers import api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RESTful API Backend cho hệ thống Quản lý Dự án và Công việc (Project & Task Management) xây dựng bằng FastAPI, SQLAlchemy và MySQL.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

setup_exception_handlers(app)

app.include_router(api_router)


@app.get(
    "/",
    tags=["Health Check"],
    summary="Kiểm tra trạng thái hệ thống và kết nối CSDL",
    description="Endpoint health check kiểm tra kết nối tới Database",
    status_code=status.HTTP_200_OK
)
def get_heal(db: Session = Depends(get_db)):
    try:
        db.connection()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Lỗi kết nối cơ sở dữ liệu server"
        )
    return {
        "message": "Kết nối database Thành công"
    }
