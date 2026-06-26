from fastapi import FastAPI

app = FastAPI()


books = [
    {"id": 1, "title": "Python Basic", "quantity": 12},
    {"id": 2, "title": "FastAPI Beginner", "quantity": 3},
    {"id": 3, "title": "Clean Code", "quantity": 5},
    {"id": 4, "title": "Database Design", "quantity": 0},
    {"id": 5, "title": "Web API Design"}
]

@app.get("/books/low-stock")
def get_books_low_stock():
    low_stock_books = [b for b in books if 0 <= b.get("quantity", -1) <= 5]
    
    if not low_stock_books:
        return {"message": "Không có sách nào sắp hết hàng", "data": []}
        
    return {"message": "Danh sách sách sắp hết hàng", "data": low_stock_books}