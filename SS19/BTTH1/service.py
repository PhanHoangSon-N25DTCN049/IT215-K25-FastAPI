from sqlalchemy.orm import Session
from fastapi import HTTPException
import models, schemas

def create_warehouse(db: Session, warehouse: schemas.WarehouseCreate):
    try:
        # Giải nén dữ liệu từ schema Pydantic V2
        db_warehouse = models.Warehouse(**warehouse.model_dump())
        db.add(db_warehouse)
        db.commit()
        db.refresh(db_warehouse)
        return db_warehouse
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database Error: " + str(e))

def get_warehouse(db: Session, warehouse_id: int):
    db_warehouse = db.query(models.Warehouse).filter(models.Warehouse.id == warehouse_id).first()
    if not db_warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    # Tự động trả về kèm list packages nhờ ORM mapping
    return db_warehouse

def update_package(db: Session, package_id: int, package_update: schemas.PackageUpdate):
    db_package = db.query(models.Package).filter(models.Package.id == package_id).first()
    if not db_package:
        raise HTTPException(status_code=404, detail="Package not found")

    try:
        # Chỉ lấy những trường thực sự được gửi lên
        update_data = package_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_package, key, value)
        
        db.commit()
        db.refresh(db_package)
        return db_package
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Update failed: " + str(e))

def delete_waybill(db: Session, waybill_id: int):
    db_waybill = db.query(models.Waybill).filter(models.Waybill.id == waybill_id).first()
    if not db_waybill:
        raise HTTPException(status_code=404, detail="Waybill not found")

    try:
        db.delete(db_waybill)
        db.commit()
        return {"message": "Xóa vật lý Vận đơn thành công"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Delete failed: " + str(e))