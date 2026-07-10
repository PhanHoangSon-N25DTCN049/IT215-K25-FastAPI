from fastapi import FastAPI
from app.database import engine, Base
from app.routers import product

# Khởi tạo bảng trong database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Product Management API")

# Gắn router
app.include_router(product.router)

@app.get("/")
def root():
    return {"message": "Welcome to Product Management API"}