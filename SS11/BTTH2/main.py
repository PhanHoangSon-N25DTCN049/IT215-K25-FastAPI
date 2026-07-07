from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# --- CẤU HÌNH DATABASE ---
# Sử dụng SQLite để chạy ngay lập tức không cần cài đặt MySQL cấu hình phức tạp
SQLALCHEMY_DATABASE_URL = "sqlite:///./all_in_one_homework.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- ĐỊNH NGHĨA MODELS (SQLAlchemy) ---
class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String(50), unique=True, index=True)
    status = Column(String(50))
    sender = Column(String(100))
    receiver = Column(String(100))

class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))

class MembershipModel(Base):
    __tablename__ = "memberships"
    id = Column(Integer, primary_key=True, index=True)
    card_number = Column(String(50), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))

class ParkingSlot(Base):
    __tablename__ = "parking_slots"
    id = Column(Integer, primary_key=True, index=True)
    slot_code = Column(String(50), unique=True, nullable=False)
    zone_name = Column(String(255), nullable=False)
    max_weight = Column(Integer, nullable=False)
    is_available = Column(Boolean, default=True)

class SmartHomePlan(Base):
    __tablename__ = "smart_home_plans"
    id = Column(Integer, primary_key=True, index=True)
    plan_code = Column(String(50), unique=True, nullable=False)
    plan_name = Column(String(255), nullable=False)
    device_quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

# Khởi tạo tất cả cấu trúc bảng trong DB
Base.metadata.create_all(bind=engine)

# --- ĐỊNH NGHĨA SCHEMAS (Pydantic Validation) ---
class MembershipCreate(BaseModel):
    card_number: str
    customer_id: int

class SlotCreate(BaseModel):
    slot_code: str
    zone_name: str = Field(..., min_length=3)
    max_weight: int

    @field_validator('max_weight')
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError('Tải trọng phải lớn hơn 0')
        return v

class PlanCreate(BaseModel):
    plan_code: str
    plan_name: str
    device_quantity: int
    price: float

    @field_validator('plan_name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Tên gói thiết bị không được để rỗng')
        return v

    @field_validator('device_quantity')
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError('Số lượng thiết bị phải lớn hơn 0')
        return v

    @field_validator('price')
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError('Đơn giá phải lớn hơn 0')
        return v

# --- DEPENDENCIES & HELPERS ---
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

app = FastAPI(title="Hệ thống API Tổng Hợp Bài Tập")

# --- ENDPOINTS ---

# 1. API Kiểm tra mã vận đơn
@app.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return {"status": 200, "message": "Success", "data": shipment}

# 2. API Đăng ký thẻ thành viên
@app.post("/memberships", status_code=status.HTTP_201_CREATED)
def create_membership(data: MembershipCreate, db: Session = Depends(get_db)):
    customer = db.query(CustomerModel).filter(CustomerModel.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Khách hàng không tồn tại trên hệ thống")
    
    existing_card = db.query(MembershipModel).filter(MembershipModel.card_number == data.card_number).first()
    if existing_card:
        raise HTTPException(status_code=400, detail="Mã số thẻ thành viên này đã được sử dụng")
    
    new_membership = MembershipModel(card_number=data.card_number, customer_id=data.customer_id)
    try:
        db.add(new_membership)
        db.commit()
        db.refresh(new_membership)
        return {
            "status": 201, 
            "message": "Success", 
            "data": {
                "id": new_membership.id, 
                "card_number": new_membership.card_number, 
                "customer_id": new_membership.customer_id
            }
        }
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Có lỗi xảy ra khi lưu dữ liệu")

# 3. API Quản lý vị trí bãi đỗ xe công nghệ
@app.post("/parking-slots", status_code=201)
def create_slot(slot: SlotCreate, db: Session = Depends(get_db)):
    try:
        new_slot = ParkingSlot(**slot.dict())
        db.add(new_slot)
        db.commit()
        db.refresh(new_slot)
        return create_response(201, "Thêm vị trí đỗ xe thành công", None, new_slot, "/parking-slots")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Mã vị trí đã tồn tại hoặc có lỗi xảy ra")

@app.get("/parking-slots")
def get_all_slots(db: Session = Depends(get_db)):
    slots = db.query(ParkingSlot).all()
    return create_response(200, "Success", None, slots, "/parking-slots")

@app.get("/parking-slots/{slot_id}")
def get_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()
    if not slot:
        return create_response(404, "Parking slot not found", "Not Found", None, f"/parking-slots/{slot_id}")
    return create_response(200, "Success", None, slot, f"/parking-slots/{slot_id}")

# 4. API Quản lý Gói Thiết bị Nhà thông minh (Smart Home Plans)
@app.post("/smart-home-plans", status_code=201)
def create_plan(plan: PlanCreate, db: Session = Depends(get_db)):
    existing_plan = db.query(SmartHomePlan).filter(SmartHomePlan.plan_code == plan.plan_code).first()
    if existing_plan:
        return create_response(
            status_code=400,
            message="Plan code already exists",
            error="Bad Request",
            data=None,
            path="/smart-home-plans"
        )
    try:
        new_plan = SmartHomePlan(
            plan_code=plan.plan_code,
            plan_name=plan.plan_name,
            device_quantity=plan.device_quantity,
            price=plan.price
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        return create_response(201, "Thêm mới thành công", None, new_plan, "/smart-home-plans")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Lỗi hệ thống khi lưu dữ liệu")

@app.get("/smart-home-plans")
def get_all_plans(db: Session = Depends(get_db)):
    plans = db.query(SmartHomePlan).all()
    return create_response(200, "Lấy danh sách thành công", None, plans, "/smart-home-plans")

@app.get("/smart-home-plans/{plan_id}")
def get_plan_by_id(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(SmartHomePlan).filter(SmartHomePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return create_response(200, "Lấy chi tiết thành công", None, plan, f"/smart-home-plans/{plan_id}")