from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import product as service
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.response import create_api_response

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("")
def read_products(request: Request, db: Session = Depends(get_db)):
    data = service.get_all(db)
    return create_api_response(request, 200, "Lấy danh sách thành công", data=data)

@router.get("/{product_id}")
def read_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    data = service.get_by_id(db, product_id)
    if not data:
        raise HTTPException(status_code=404, detail="Product not found")
    return create_api_response(request, 200, "Lấy sản phẩm thành công", data=data)

@router.post("")
def create_product(product: ProductCreate, request: Request, db: Session = Depends(get_db)):
    data = service.create(db, product.model_dump())
    return create_api_response(request, 201, "Thêm sản phẩm thành công", data=data)

@router.put("/{product_id}")
def update_product(product_id: int, product: ProductUpdate, request: Request, db: Session = Depends(get_db)):
    db_product = service.get_by_id(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    data = service.update(db, db_product, product.model_dump(exclude_unset=True))
    return create_api_response(request, 200, "Cập nhật thành công", data=data)

@router.delete("/{product_id}")
def delete_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    db_product = service.get_by_id(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    service.delete(db, db_product)
    return create_api_response(request, 200, "Xóa thành công")