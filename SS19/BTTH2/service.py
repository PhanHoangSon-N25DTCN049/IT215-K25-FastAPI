from sqlalchemy.orm import Session
from fastapi import HTTPException
import models, schemas

def create_clinic(db: Session, clinic: schemas.ClinicCreate):
    try:
        db_clinic = models.Clinic(**clinic.model_dump())
        db.add(db_clinic)
        db.commit()
        db.refresh(db_clinic)
        return db_clinic
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database Error: " + str(e))

def get_clinic(db: Session, clinic_id: int):
    db_clinic = db.query(models.Clinic).filter(models.Clinic.id == clinic_id).first()
    if not db_clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return db_clinic

def update_doctor(db: Session, doctor_id: int, doctor_update: schemas.DoctorUpdate):
    db_doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not db_doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    try:
        # Cập nhật động: chỉ lấy những giá trị được truyền vào
        update_data = doctor_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_doctor, key, value)
        
        db.commit()
        db.refresh(db_doctor)
        return db_doctor
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Update failed: " + str(e))

def delete_license(db: Session, license_id: int):
    db_license = db.query(models.License).filter(models.License.id == license_id).first()
    if not db_license:
        raise HTTPException(status_code=404, detail="License not found")

    try:
        db.delete(db_license)
        db.commit()
        return {"message": "Đã xóa vĩnh viễn Chứng chỉ hành nghề khỏi hệ thống"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Delete failed: " + str(e))