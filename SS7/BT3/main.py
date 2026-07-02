from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

products_db = [
    {"id": 101, "name": "Bàn phím cơ", "stock": 5, "price": 1200000.0},
    {"id": 102, "name": "Chuột Gaming", "stock": 2, "price": 600000.0}
]
orders_db = []

app = FastAPI()

class RequestOrder(BaseModel):
    product_id:int
    quantity: int
    
@app.get("/orders")
def get_orders():
    return orders_db

@app.post("/orders", status_code=status.HTTP_200_OK)
def create_orders(order:RequestOrder):
    product_order = next((p for p in products_db if p["id"] == order.product_id), None)
    if not product_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found!")
    if order.quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Số lượng mua phải lớn hơn 0")
    if product_order["stock"] < order.quantity:
        raise  HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sản phẩm không đủ số lượng trong kho")
    
    product_order["stock"] -= order.quantity
    
    new_order = {
        "id_order": max((o["id"] for o in orders_db), default=0) + 1,
        "id_product": order.product_id,
        "product_name": product_order["name"],
        "quantity": order.quantity,
        "total_price": product_order["price"] * order.quantity
    }
    
    orders_db.append(new_order)
    return {
        "status":"success",
        "message":"Tạo đơn hàng thành công",
        "data":new_order
    }