from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

products = [
    {"id": 1, "code": "SP001", "name": "Keyboard", "price": 500000, "stock": 10},
    {"id": 2, "code": "SP002", "name": "Mouse", "price": 300000, "stock": 5}
]

class ProductUpdate(BaseModel):
    code: str
    name: str
    price: float
    stock: int

@app.get("/products")
def get_products():
    return products

@app.put("/products/{product_id}")
def update_product(product_id: int, product_data: ProductUpdate):
    target_product = next((p for p in products if p["id"] == product_id), None)
    if not target_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    
    if any(p["code"] == product_data.code and p["id"] != product_id for p in products):
        raise HTTPException(status_code=409, detail="Product code already exists")
    
    target_product.update(product_data.dict())
    
    return {"message": "Update successfully", "data": target_product}