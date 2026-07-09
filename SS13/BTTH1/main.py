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
from typing import Any
from datetime import datetime
from http import HTTPStatus


DATABASE_URL = "sqlite:///./btth.db"
engine = create_engine(DATABASE_URL)
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
# Base = declarative_base()

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dish_code = Column(String(50), unique=True, nullable=False, index=True)
    dish_name = Column(String(100), nullable=False)
    calorie_count = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(30), default="AVAILABLE", nullable=False)

Base.metadata.create_all(engine)

class CreateDish(BaseModel):
    dish_code: str = Field(max_length=50)
    dish_name: str = Field(max_length=100)
    calorie_count: int
    price: float
    
class UpdateDish(BaseModel):
    dish_name: str | None =  Field(default=None, max_length=100)
    calorie_count: int | None = None
    price: float | None = None
    status: str = Field(default=None, max_length=30)

class APIResponse(BaseModel):
    statusCode: int
    message: str
    error: Any
    data: Any
    path: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

def api_response(request: Request, statusCode:int, message: str, error: Any = None, data: Any = None):
    return {
        "statusCode": statusCode,
        "message": message,
        "error": error,
        "data": data,
        "path": request.url.path,
    }

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
            "timestamp": datetime.now().isoformat()
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
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/database/health", status_code=status.HTTP_200_OK, tags=["Health"])
def get_health_database(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể kết nối database"
        )
    else:
        return {
            "message":"Kết nối database thành công"
        }
        

@app.post("/menu-items", status_code=status.HTTP_201_CREATED, tags=["Menu"], response_model=APIResponse)
def create_dish(dish: CreateDish, request: Request, db: Session = Depends(get_db)):
    try:
        dish_new = MenuItem(**dish.model_dump())
        db.add(dish_new)
        db.commit()
        db.refresh(dish_new)
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail= f"Mã món ăn đã tồn tại"
        )
    except Exception:
        db.rollback()
        raise HTTPException (
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"Gặp lỗi khi lưu dữ liệu"
        )
    else:
        return api_response(request,statuscode=201, message="Thêm món ăn thành công", data=jsonable_encoder(dish_new))
    
@app.get("/menu-items", status_code=status.HTTP_200_OK, tags=["Menu"], response_model=APIResponse)
def get_all_menu(request: Request, db: Session = Depends(get_db)):
    list_menu = db.query(MenuItem).all()
    return api_response(request, statuscode=200, message="Lấy danh sách toàn bộ món ăn thành công", data=jsonable_encoder(list_menu))

@app.get("/menu-items/{item_id}", status_code=status.HTTP_200_OK, tags=["Menu"], response_model=APIResponse)
def get_dish_by_id(request: Request, item_id: int, db: Session = Depends(get_db)):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Menu item not found"
        )
    return api_response(request, statuscode=200, message="Lấy món ăn thành công", data=jsonable_encoder(item))
    
@app.put("/menu-items/{item_id}", status_code=status.HTTP_200_OK, tags=["Menu"], response_model=APIResponse)
def update_dish(request: Request, item_id:int, data: UpdateDish, db: Session = Depends(get_db)):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    try:
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item,key, value)
        
        db.commit()
        db.refresh(item)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"Lỗi: {e}"
        )
    else:
        return api_response(request, statuscode=200, message="Cập nhật món ăn thành công", data=jsonable_encoder(item))
    
    
@app.delete("/menu-items/{item_id}", status_code=status.HTTP_200_OK, tags=["Menu"], response_model=APIResponse)
def del_dish(request: Request, item_id: int, db: Session = Depends(get_db)):
    item_del = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item_del:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )
    try:
        db.delete(item_del)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException (
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi: {e}"
        )
    return api_response(request, statuscode=200, message="Xóa món ăn thành công")
        