from fastapi import FastAPI
app = FastAPI()

books = [
    {
        "id": 1,
        "title": "Python Basic",
        "author": "Nguyen Van A",
        "category": "programming",
        "year": 2022,
        "is_available": True
    },
    {
        "id": 2,
        "title": "Web API Design",
        "author": "Tran Van B",
        "category": "web",
        "year": 2021,
        "is_available": False
    },
    {
        "id": 3,
        "title": "Database Management System",
        "author": "Phan Van C",
        "category": "database",
        "year": 2020,
        "is_available": True
    },
    {
        "id": 4,
        "title": "Network Essentials",
        "author": "Le Van D",
        "category": "network",
        "year": 2018,
        "is_available": True
    },
    {
        "id": 5,
        "title": "Advanced Programming",
        "author": "Hoang Van E",
        "category": "programming",
        "year": 2022,
        "is_available": False
    },
    {
        "id": 6,
        "title": "FastAPI Basic",
        "author": "Nguyen Van A",
        "category": "web",
        "year": 2023,
        "is_available": True
    }
]

@app.get("/books/statistics")
def get_statistics():
    total_books = len(books)
    available_books = len([book for book in books if book["is_available"]])
    borrowed_books = len([book for book in books if not book["is_available"]])
    
    return {
                "total_books": total_books,
                "available_books": available_books,
                "borrowed_books": borrowed_books
            }
    
@app.get("/books/categories")
def get_categories():
    categories = list({book["category"] for book in books})
    return {
        "categories": categories
    }
    
@app.get("/books/latest")
def get_book_latest():
    latest_book = max(books, key=lambda book: book["year"], default={"message": "No books available"})
    return latest_book