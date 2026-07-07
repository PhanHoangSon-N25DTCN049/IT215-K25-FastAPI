from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# --- 1. Thiết lập Database (Giả định dùng SQLite cho bài test) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" 
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Định nghĩa Model ---
class CustomerModel(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))

class MembershipModel(Base):
    __tablename__ = "memberships"
    id = Column(Integer, primary_key=True, index=True)
    card_number = Column(String(50), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))

# Tạo bảng (chỉ dùng cho môi trường dev)
Base.metadata.create_all(bind=engine)

# --- 3. Schema Pydantic ---
class MembershipCreate(BaseModel):
    card_number: str
    customer_id: int

# --- 4. Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. API Endpoint ---
app = FastAPI()

@app.post("/memberships", status_code=status.HTTP_201_CREATED)
def create_membership(data: MembershipCreate, db: Session = Depends(get_db)):
    # Bước 1: Kiểm tra khách hàng tồn tại
    customer = db.query(CustomerModel).filter(CustomerModel.id == data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=404, 
            detail="Khách hàng không tồn tại trên hệ thống"
        )
    
    # Bước 2: Kiểm tra trùng mã thẻ
    existing_card = db.query(MembershipModel).filter(MembershipModel.card_number == data.card_number).first()
    if existing_card:
        raise HTTPException(
            status_code=400, 
            detail="Mã số thẻ thành viên này đã được sử dụng"
        )
    
    # Bước 3: Thực hiện tạo mới
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