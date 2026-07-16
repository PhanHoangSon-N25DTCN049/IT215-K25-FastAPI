from fastapi import FastAPI, status, HTTPException, Depends
from database import get_db
from sqlalchemy.orm import Session
from schemas import *
from service import *

app = FastAPI(title="Clinic Management API")

@app.post("/clinics", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
def create_clinics_app(clinic_data: ClinicCreate, db: Session = Depends(get_db)):
    try:
        new_clinic = create_clinic(db, clinic_data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi thêm dữ liệu vào database"
        )
    return new_clinic

@app.get("/clinics/{clinic_id}", status_code= status.HTTP_200_OK, response_model=ClinicDetailResponse)
def get_clinic_app(clinic_id: int, db: Session = Depends(get_db)):
    query = get_clinic_by_id(db,clinic_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic Not Found!"
        )
    return query

@app.post("/doctors", status_code=status.HTTP_201_CREATED, response_model=DoctorResponse)
def create_doctor_app(doctor_data: DoctorCreate, db:Session = Depends(get_db)):
    clinic = get_clinic_by_id(db, doctor_data.clinic_id)
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phòng khám không tồn tại"
        )
    
    existing_doctor = db.query(Doctor).filter(Doctor.doctor_code == doctor_data.doctor_code).first()
    if existing_doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã bác sĩ đã tồn tại"
        )
        
    try:
        new_doctor = create_doctor(db, doctor_data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi thêm dữ liệu vào database"
        )
    return new_doctor

@app.get("/doctors/{doctor_id}", status_code=status.HTTP_200_OK, response_model=DoctorResponse)
def get_doctor(doctor_id: int, db: Session =Depends(get_db)):
    query = get_doctor_by_id(db,doctor_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor Not Found!"
        )
    return query

@app.patch("/doctors/{doctor_id}", response_model=DoctorResponse)
def update_doctor_endpoint(
    doctor_id: int, 
    doctor_update: DoctorUpdate, 
    db: Session = Depends(get_db)
):
    db_doctor = get_doctor_by_id(db, doctor_id)
    if not db_doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Không tìm thấy bác sĩ"
        )
    
    if doctor_update.clinic_id is not None:
        clinic = get_clinic_by_id(db, doctor_update.clinic_id)
        if not clinic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phòng khám không tồn tại"
            )
            
    if doctor_update.doctor_code is not None:
        existing_doctor = db.query(Doctor).filter(
            Doctor.doctor_code == doctor_update.doctor_code,
            Doctor.id != doctor_id
        ).first()
        if existing_doctor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã bác sĩ đã tồn tại"
            )

    updated_doctor = update_doctor(db=db, doctor_id=doctor_id, doctor_update=doctor_update)
    return updated_doctor

@app.delete("/licenses/{license_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_license_endpoint(
    license_id: int, 
    db: Session = Depends(get_db)
):
    is_deleted = delete_license(db=db, license_id=license_id)
    
    if not is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="License not found"
        )
        
    return