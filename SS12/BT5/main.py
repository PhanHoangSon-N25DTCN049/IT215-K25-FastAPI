from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 1. Cấu hình kết nối Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./homeword.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Định nghĩa Model
class DiscountModel(Base):
    __tablename__ = "discounts"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False)

# 3. Hàm Dependency lấy Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 4. Hàm Service xử lý xóa
def delete_discount_service(db: Session, discount_id: int):
    # Tìm mã giảm giá
    discount = db.query(DiscountModel).filter(DiscountModel.id == discount_id).first()
    
    # Kiểm tra tồn tại (Quy tắc 1 & 2)
    if not discount:
        return None
        
    # Xóa và commit (Quy tắc 3)
    db.delete(discount)
    db.commit()
    return discount

# 5. Khởi tạo FastAPI và Router
app = FastAPI()

@app.delete("/discounts/{discount_id}", status_code=status.HTTP_200_OK)
def delete_discount(discount_id: int, db: Session = Depends(get_db)):
    # Gọi hàm service (Quy tắc 4)
    result = delete_discount_service(db, discount_id)
    
    # Xử lý phản hồi khi không tồn tại
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Mã giảm giá với ID {discount_id} không tồn tại."
        )
        
    return {"message": "Xóa mã giảm giá thành công", "id": discount_id}