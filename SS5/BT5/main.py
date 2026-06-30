from fastapi import FastAPI, HTTPException, status

products = [
    {"id": 1, "code": "SP001", "name": "Keyboard", "price": 500000, "is_active": True},
    {"id": 2, "code": "SP002", "name": "Mouse", "price": 300000, "is_active": True},
    {"id": 3, "code": "SP003", "name": "Monitor", "price": 2500000, "is_active": False}
]

app = FastAPI()

@app.delete("/products/{product_id}")
def del_product(product_id:int):
    product = next((p for p in products if p["id"] == product_id),None)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    if product["is_active"] == False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already inactive"
        )
    product["is_active"] = False
    return {
        "message":"Ngừng kinh doanh thành công"
    }