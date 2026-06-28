from fastapi import FastAPI

books = [
    {"id": 1,
    "title": "Python Basic",
    "author": "Nguyen Van A",
    "category": "programming",
    "year": 2022,
    "is_available": True},
    
    {"id": 2,
    "title": "Web API Design",
    "author": "Tran Van B",
    "category": "web",
    "year": 2021,
    "is_available": False}
]

app = FastAPI()

@app.get("/books/available")
def get_book_available():
    list_return = [book for book in books if book["is_available"]]
    return list_return

@app.get("/books/borrowed")
def get_borrowed():
    list_return = [book for book in books if not book["is_available"]]
    return list_return