from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

products = [
    {"id": 1, "code": "SP001", "name": "Laptop Dell", "price": 15000000, "stock": 10},
    {"id": 2, "code": "SP002", "name": "Mouse Logitech", "price": 350000, "stock": 50}
]

class ProductCreate(BaseModel):
    code: str
    name: str
    price: float
    stock: int

@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    for item in products:
        if item["code"] == product.code:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Sản phẩm với mã {product.code} đã tồn tại."
            )
            
    new_product = {
        "id": len(products) + 1,
        "code": product.code,
        "name": product.name,
        "price": product.price,
        "stock": product.stock
    }
    products.append(new_product)
    
    return {
        "message": "Create product successfully",
        "data": new_product
    }