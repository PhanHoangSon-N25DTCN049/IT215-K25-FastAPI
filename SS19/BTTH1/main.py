from fastapi import FastAPI, Depends, status
from sqlalchemy.orm import Session
import models, schemas, service
from database import engine, get_db

# Khởi tạo các bảng vào CSDL (có thể dùng Alembic sau nếu cần)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Supply Chain API")

@app.post("/warehouses", response_model=schemas.WarehouseDetailResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(warehouse: schemas.WarehouseCreate, db: Session = Depends(get_db)):
    return service.create_warehouse(db=db, warehouse=warehouse)

@app.get("/warehouses/{warehouse_id}", response_model=schemas.WarehouseDetailResponse, status_code=status.HTTP_200_OK)
def read_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    return service.get_warehouse(db=db, warehouse_id=warehouse_id)

@app.patch("/packages/{package_id}", response_model=schemas.PackageDetail, status_code=status.HTTP_200_OK)
def update_package(package_id: int, package: schemas.PackageUpdate, db: Session = Depends(get_db)):
    return service.update_package(db=db, package_id=package_id, package_update=package)

@app.delete("/waybills/{waybill_id}", status_code=status.HTTP_200_OK)
def delete_waybill(waybill_id: int, db: Session = Depends(get_db)):
    return service.delete_waybill(db=db, waybill_id=waybill_id)
