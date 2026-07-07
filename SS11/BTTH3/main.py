from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH DATABASE
# ==========================================
# Dùng tạm SQLite để test nhanh, bạn có thể đổi thành MySQL theo format:
# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@localhost/db_name"
SQLALCHEMY_DATABASE_URL = "sqlite:///./medical_devices.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. ĐỊNH NGHĨA MODEL CƠ SỞ DỮ LIỆU
# ==========================================
class MedicalDevice(Base):
    __tablename__ = "medical_devices"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    device_code = Column(String(50), unique=True, nullable=False, index=True)
    device_name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    status = Column(String(20), default="ACTIVE")

# Tạo bảng
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. SCHEMAS (PYDANTIC VALIDATION)
# ==========================================
class DeviceCreate(BaseModel):
    device_code: str
    device_name: str = Field(..., min_length=3)
    department: str
    status: Literal['ACTIVE', 'INACTIVE'] = 'ACTIVE'

    @field_validator('department')
    def validate_department(cls, v):
        if not v or not v.strip():
            raise ValueError('Khoa/Phòng không được để rỗng')
        return v.strip()

# ==========================================
# 4. KHỞI TẠO APP & CẤU HÌNH EXCEPTION HANDLER
# ==========================================
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_response(status_code: int, message: str, error: str | None, data: any, path: str):
    return {
        "statusCode": status_code,
        "message": message,
        "error": error,
        "data": data,
        "path": path,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# Ghi đè Exception mặc định của FastAPI để trả về đúng 6 trường quy chuẩn
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    error_type = "Not Found" if exc.status_code == 404 else "Bad Request"
    return JSONResponse(
        status_code=exc.status_code,
        content=create_response(exc.status_code, exc.detail, error_type, None, request.url.path)
    )

# ==========================================
# 5. API ENDPOINTS
# ==========================================

# Thêm mới thiết bị y tế
@app.post("/devices", status_code=201)
def create_device(device: DeviceCreate, request: Request, db: Session = Depends(get_db)):
    # Kiểm tra mã thiết bị tồn tại
    existing_device = db.query(MedicalDevice).filter(MedicalDevice.device_code == device.device_code).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Mã thiết bị đã tồn tại trong hệ thống")
    
    try:
        new_device = MedicalDevice(
            device_code=device.device_code,
            device_name=device.device_name,
            department=device.department,
            status=device.status
        )
        db.add(new_device)
        db.commit()
        db.refresh(new_device)
        
        return create_response(201, "Thêm thiết bị y tế thành công", None, new_device, request.url.path)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi lưu dữ liệu")

# Lấy danh sách toàn bộ thiết bị
@app.get("/devices")
def get_all_devices(request: Request, db: Session = Depends(get_db)):
    devices = db.query(MedicalDevice).all()
    return create_response(200, "Lấy danh sách thành công", None, devices, request.url.path)

# Lấy thông tin chi tiết
@app.get("/devices/{device_id}")
def get_device_by_id(device_id: int, request: Request, db: Session = Depends(get_db)):
    device = db.query(MedicalDevice).filter(MedicalDevice.id == device_id).first()
    
    if not device:
        # Bắt buộc raise theo yêu cầu đề bài, exception_handler ở trên sẽ tự chuyển sang cấu trúc 6 trường
        raise HTTPException(status_code=404, detail="Device not found")
        
    return create_response(200, "Lấy chi tiết thiết bị thành công", None, device, request.url.path)