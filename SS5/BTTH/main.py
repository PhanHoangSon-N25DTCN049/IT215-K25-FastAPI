from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
products = [

    {"id": 1, "name": "Keyboard", "price": 500000},

    {"id": 2, "name": "Mouse", "price": 300000}

]

app = FastAPI()

class CreateProduct(BaseModel):
    name:str = Field(...)
    price: float = Field(..., gt=0)
    
@app.get("/products")
def get_products():
    return products


@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: CreateProduct):
    new_product = {
        "id": max(products, key= lambda product: product["id"])["id"] + 1,
        "name" : product.name,
        "price": product.price
    }
    products.append(new_product)
    return {
        "status": "success",
        "message": "Tạo sản phẩm thành công",
        "data": new_product
    }

@app.delete("/products/{product_id}")
def del_product(product_id:int):
    product = next((p for p in products if p["id"] == product_id), None)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    products.remove(product)
    return {"message": "Xóa thành công"}