from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import Base, engine
import src.models  # Đảm bảo các ORM models được nạp vào metadata
from src.exceptions import setup_exception_handlers
from src.middlewares.rbac import RBACMiddleware
from src.routers.api import api_router

# Tự động tạo bảng nếu chưa có
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Đảm bảo tables được tạo khi server khởi động
    Base.metadata.create_all(bind=engine)
    yield
    # Dọn dẹp tài nguyên (nếu có) khi tắt ứng dụng


app = FastAPI(
    title="MegaMart ERP Backend API",
    description="Hệ thống Backend ERP bảo mật với RBAC Middleware và CORS Policy nghiêm ngặt",
    version="1.0.0",
    lifespan=lifespan,
)

# Đăng ký các custom exception handlers
setup_exception_handlers(app)

# 1. Đăng ký Middleware Phân quyền tập trung (RBAC)
app.add_middleware(RBACMiddleware)

# 2. Cấu hình CORS Policy nghiêm ngặt (Vá lỗ hổng Cross-Site Attack)
ALLOWED_ORIGINS = [
    "https://internal.megamart.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-User-Role"],
)

# Đăng ký các router
app.include_router(api_router)


@app.get("/", tags=["Health Check"])
def root():
    return {
        "message": "Welcome to FastAPI Application!",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok"}
