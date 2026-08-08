from fastapi import FastAPI, Depends, status
from database import get_db

library =  {
"ten_thu_vien": "Thư viện Rikkei",
"dia_chi": "123 Nguyễn Văn Cừ, Hà Nội",
"gio_mo_cua": "08:00 - 21:00"
}
app = FastAPI()


@app.get("/api/v1/library-info", status_code=status.HTTP_200_OK)
def get_library():
    return library
