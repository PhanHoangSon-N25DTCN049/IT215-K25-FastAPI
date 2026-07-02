from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

# Dữ liệu nội bộ trong bộ nhớ tạm - Chứa các trường nhạy cảm
orders_db = [
    {
        "id": 1,
        "customer_name": "Nguyen Van A",
        "total_amount": 1500000.0,
        "profit_margin": 0.25,      # Nhạy cảm - Cấm lộ!
        "supplier_id": "SUP_DELL_01" # Nhạy cảm - Cấm lộ!
    },
    {
        "id": 2,
        "customer_name": "Tran Thi B",
        "total_amount": 350000.0,
        "profit_margin": 0.30,       # Nhạy cảm - Cấm lộ!
        "supplier_id": "SUP_LOGI_02"  # Nhạy cảm - Cấm lộ!
    }
]

class OrderInternal(BaseModel):
    id: int
    customer_name: str
    total_amount: float
    profit_margin: float
    supplier_id: str
    
class OrderPublic(BaseModel):
    id: int
    customer_name: str
    total_amount: float

@app.get("/orders/{order_id}", response_model=OrderPublic)
def get_order_detail(order_id: int):
    for order in orders_db:
        if order["id"] == order_id:
            return order 
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")