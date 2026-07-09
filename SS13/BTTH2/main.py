from sqlalchemy import Column, Integer, String, Float
from fastapi import FastAPI, status, HTTPException, Depends, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime
from http import HTTPStatus

DATABASE_URL = "sqlite:///./pet_boarding.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    pass

# 1. SQLAlchemy Model
class BoardingSlot(Base):
    __tablename__ = "boarding_slots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    slot_number = Column(String(50), unique=True, nullable=False, index=True)
    room_size = Column(String(30), nullable=False)
    price_per_day = Column(Float, nullable=False)
    status = Column(String(30), default="VACANT", nullable=False)

Base.metadata.create_all(engine)

# 2. Pydantic Schemas
class CreateSlot(BaseModel):
    slot_number: str = Field(max_length=50)
    room_size: Literal["SMALL", "MEDIUM", "LARGE"]
    price_per_day: float = Field(gt=0)
    
class UpdateSlot(BaseModel):
    slot_number: str | None = Field(default=None, max_length=50)
    room_size: Literal["SMALL", "MEDIUM", "LARGE"] | None = None
    price_per_day: float | None = Field(default=None, gt=0)
    status: Literal["VACANT", "OCCUPIED"] | None = None

# 3. Response Schema
class APIResponse(BaseModel):
    statusCode: int
    message: str
    error: Any
    data: Any
    path: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat() + "Z")

def api_response(request: Request, statusCode: int, message: str, error: Any = None, data: Any = None):
    return {
        "statusCode": statusCode,
        "message": message,
        "error": error,
        "data": data,
        "path": request.url.path,
        "timestamp": datetime.now().isoformat() + "Z"
    }

# 4. Exception Handlers
@app.exception_handler(StarletteHTTPException)
def customer_http_exception(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "statusCode": exc.status_code,
            "message": exc.detail,
            "error": HTTPStatus(exc.status_code).phrase,
            "data": None,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat() + "Z"
        }
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "statusCode": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Dữ liệu đầu vào không hợp lệ",
            "error": exc.errors(),
            "data": None,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat() + "Z"
        }
    )

# 5. CRUD Endpoints
@app.post("/boarding-slots", status_code=status.HTTP_201_CREATED, tags=["Boarding Slots"], response_model=APIResponse)
def create_slot(slot: CreateSlot, request: Request, db: Session = Depends(get_db)):
    try:
        slot_new = BoardingSlot(**slot.model_dump())
        db.add(slot_new)
        db.commit()
        db.refresh(slot_new)
    except IntegrityError:
        db.rollback()
        # Trả về 400 Bad Request nếu trùng mã khoang theo yêu cầu đề bài
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot number already exists"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gặp lỗi khi lưu dữ liệu: {e}"
        )
    return api_response(request, statusCode=200, message="Thêm khoang lưu trú thành công", data=jsonable_encoder(slot_new))

@app.get("/boarding-slots", status_code=status.HTTP_200_OK, tags=["Boarding Slots"], response_model=APIResponse)
def get_all_slots(request: Request, db: Session = Depends(get_db)):
    slots = db.query(BoardingSlot).all()
    return api_response(request, statusCode=200, message="Lấy danh sách thành công", data=jsonable_encoder(slots))

@app.get("/boarding-slots/{slot_id}", status_code=status.HTTP_200_OK, tags=["Boarding Slots"], response_model=APIResponse)
def get_slot_by_id(request: Request, slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(BoardingSlot).filter(BoardingSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy khoang lưu trú"
        )
    return api_response(request, statusCode=200, message="Lấy chi tiết thành công", data=jsonable_encoder(slot))

@app.put("/boarding-slots/{slot_id}", status_code=status.HTTP_200_OK, tags=["Boarding Slots"], response_model=APIResponse)
def update_slot(request: Request, slot_id: int, data: UpdateSlot, db: Session = Depends(get_db)):
    slot = db.query(BoardingSlot).filter(BoardingSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy khoang lưu trú"
        )
    try:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(slot, key, value)
        
        db.commit()
        db.refresh(slot)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slot number already exists"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gặp lỗi khi cập nhật dữ liệu: {e}"
        )
    return api_response(request, statusCode=200, message="Cập nhật thành công", data=jsonable_encoder(slot))

@app.delete("/boarding-slots/{slot_id}", status_code=status.HTTP_200_OK, tags=["Boarding Slots"], response_model=APIResponse)
def delete_slot(request: Request, slot_id: int, db: Session = Depends(get_db)):
    slot_del = db.query(BoardingSlot).filter(BoardingSlot.id == slot_id).first()
    if not slot_del:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy khoang lưu trú"
        )
    try:
        db.delete(slot_del)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gặp lỗi khi xóa dữ liệu: {e}"
        )
    return api_response(request, statusCode=200, message="Xóa khoang lưu trú thành công")