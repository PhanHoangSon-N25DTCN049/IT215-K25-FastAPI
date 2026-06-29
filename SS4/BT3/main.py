from fastapi import FastAPI, Query
products = [
    {"id": 1, "name": "Laptop", "price": 15000000},
    {"id": 2, "name": "Mouse", "price": 200000},
    {"id": 3, "name": "Keyboard", "price": 500000},
    {"id": 4, "name": "Monitor", "price": 3000000}
]
app = FastAPI()

@app.get("/products")
def get_products(max_price: float | None =  Query(default=None), keyword: str | None = Query(default=None)):
    if max_price is not None and max_price < 0:
        return {"detail": "max_price không được âm"}
    list_products = list(products)
    if keyword:
        list_products = [item for item in list_products if keyword.lower() in item["name"].lower()]
    if max_price is not None:
        list_products = [item for item in list_products if item["price"] <= max_price]
    
    if not list_products:
        return {
            "message":"Không tìm thấy sản phẩm"
        } 
    return list_products