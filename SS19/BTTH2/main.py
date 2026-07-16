from fastapi import FastAPI, Depends, status
from sqlalchemy.orm import Session
import models, schemas, service
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Healthcare Management API")

@app.post("/clinics", response_model=schemas.ClinicDetailResponse, status_code=status.HTTP_201_CREATED)
def create_clinic(clinic: schemas.ClinicCreate, db: Session = Depends(get_db)):
    return service.create_clinic(db=db, clinic=clinic)

@app.get("/clinics/{clinic_id}", response_model=schemas.ClinicDetailResponse, status_code=status.HTTP_200_OK)
def read_clinic(clinic_id: int, db: Session = Depends(get_db)):
    return service.get_clinic(db=db, clinic_id=clinic_id)

@app.patch("/doctors/{doctor_id}", response_model=schemas.DoctorDetail, status_code=status.HTTP_200_OK)
def update_doctor(doctor_id: int, doctor: schemas.DoctorUpdate, db: Session = Depends(get_db)):
    return service.update_doctor(db=db, doctor_id=doctor_id, doctor_update=doctor)

@app.delete("/licenses/{license_id}", status_code=status.HTTP_200_OK)
def delete_license(license_id: int, db: Session = Depends(get_db)):
    return service.delete_license(db=db, license_id=license_id)