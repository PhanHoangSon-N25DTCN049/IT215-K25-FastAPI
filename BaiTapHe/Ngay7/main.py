from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class Book(BaseModel):
    id: int
    ten_sach: str
    tac_gia: str
    nam_xuat_ban: int
    so_luong: int

class BookUpdate(BaseModel):
    ten_sach: str
    tac_gia: str
    nam_xuat_ban: int
    so_luong: int

danh_sach_sach: List[Book] = [
    Book(id=1, ten_sach="Nhà Giả Kim", tac_gia="Paulo Coelho", nam_xuat_ban=1988, so_luong=5),
    Book(id=2, ten_sach="Dế Mèn Phiêu Lưu Ký", tac_gia="Tô Hoài", nam_xuat_ban=1941, so_luong=8),
    Book(id=3, ten_sach="Kính Vạn Hoa", tac_gia="Nguyễn Nhật Ánh", nam_xuat_ban=1995, so_luong=12)
]

@app.post("/api/v1/books", response_model=Book)
def create_book(book: Book):
    for existing_book in danh_sach_sach:
        if existing_book.id == book.id:
            raise HTTPException(status_code=400, detail=f"Sách với id {book.id} đã tồn tại.")
    
    danh_sach_sach.append(book)
    return book

@app.get("/api/v1/books", response_model=List[Book])
def get_all_books():
    return danh_sach_sach

@app.get("/api/v1/books/{book_id}", response_model=Book)
def get_book_by_id(book_id: int):
    for book in danh_sach_sach:
        if book.id == book_id:
            return book
            
    raise HTTPException(
        status_code=404, 
        detail=f"Không tìm thấy sách với id: {book_id}"
    )

@app.put("/api/v1/books/{book_id}", response_model=Book)
def update_book(book_id: int, updated_data: BookUpdate):
    for index, book in enumerate(danh_sach_sach):
        if book.id == book_id:
            updated_book = Book(
                id=book_id,
                ten_sach=updated_data.ten_sach,
                tac_gia=updated_data.tac_gia,
                nam_xuat_ban=updated_data.nam_xuat_ban,
                so_luong=updated_data.so_luong
            )
            danh_sach_sach[index] = updated_book
            return updated_book
            
    raise HTTPException(
        status_code=404, 
        detail=f"Không tìm thấy sách với id: {book_id}"
    )

@app.delete("/api/v1/books/{book_id}")
def delete_book(book_id: int):
    for index, book in enumerate(danh_sach_sach):
        if book.id == book_id:
            deleted_book = danh_sach_sach.pop(index)
            return {"message": "Đã xóa sách thành công", "book": deleted_book}
            
    raise HTTPException(
        status_code=404, 
        detail=f"Không tìm thấy sách với id: {book_id}"
    )