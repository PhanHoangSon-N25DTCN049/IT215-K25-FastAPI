from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH DATABASE
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./night_project.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. ĐỊNH NGHĨA MODELS (SQLAlchemy)
# ==========================================
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

# Khởi tạo bảng trong Database
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. ĐỊNH NGHĨA SCHEMAS (Pydantic)
# ==========================================
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

# ==========================================
# 4. DEPENDENCIES & HELPERS
# ==========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_response(status_code, message, error, data, path):
    return {
        "statusCode": status_code,
        "message": message,
        "error": error,
        "data": data,
        "path": path,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# Khởi tạo ứng dụng
app = FastAPI(title="Tổng hợp API Project")

# ==========================================
# 5. ENDPOINTS
# ==========================================

# --- API 1: Kiểm tra mã vận đơn ---
@app.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return {"status": 200, "message": "Success", "data": shipment}

# --- API 2: Đăng ký thẻ thành viên ---
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

# --- API 3: Quản lý bãi đỗ xe công nghệ ---
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