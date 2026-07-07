from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
# Giả định đã có file database.py và models.py theo cấu trúc project
from .database import get_db
from .models import Shipment

app = FastAPI()

@app.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    # Tối ưu: Dùng .filter().first() để chặn sớm từ Database
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    
    if not shipment:
        # Xử lý lỗi sạch sẽ, không lộ lỗi hệ thống
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    return {
        "status": 200, 
        "message": "Success", 
        "data": shipment
    }