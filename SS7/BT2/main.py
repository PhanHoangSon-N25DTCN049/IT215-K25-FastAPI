from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Literal

app = FastAPI()

orders_db = [
    {"id": 1, "customer_name": "Nguyen Van A", "status": "PENDING"},
    {"id": 2, "customer_name": "Tran Thi B", "status": "SHIPPING"}
]

class StatusUpdate(BaseModel):
    status: Literal["PENDING", "SHIPPING", "DELIVERED"]

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    return next((o for o in orders_db if o["id"] == order_id), None)

@app.put("/orders/{order_id}/status")
def update_order_status(order_id: int, data: StatusUpdate):
    order = next((o for o in orders_db if o["id"] == order_id), None)
    
    if not order:
        raise  HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found!")
        
    order["status"] = data.status

    return {"statusCode":status.HTTP_200_OK , "message": "Cập nhật thành công", "data": order}