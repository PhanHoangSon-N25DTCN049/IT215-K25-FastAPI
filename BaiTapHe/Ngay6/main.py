from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class BookCreate(BaseModel):
    title: str
    author: str
    price: float
    pages: int

class BookResponse(BookCreate):
    id: int



books_db = []
book_id_counter = 1

@app.post("/books", response_model=BookResponse)
def create_book(book: BookCreate):
    global book_id_counter
    
    new_book = BookResponse(
        id=book_id_counter,
        title=book.title,
        author=book.author,
        price=book.price,
        pages=book.pages
    )
    
    books_db.append(new_book)
    
    book_id_counter += 1
    
    return new_book

@app.get("/books/{id}", response_model=BookResponse)
def get_book(id: int):
    for book in books_db:
        if book.id == id:
            return book
            
    raise HTTPException(status_code=404, detail="Book not found")