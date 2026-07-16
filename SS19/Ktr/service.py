from sqlalchemy.orm import Session
from schemas import *
from models import *


def create_clinic(db: Session, clinic_data: ClinicCreate) -> Clinic:
    new_clinic = Clinic(**clinic_data.model_dump())
    db.add(new_clinic)
    db.commit()
    db.refresh(new_clinic)
    return new_clinic
    
def get_clinic_by_id(db: Session, clinic_id: int) -> Optional[Clinic]:
    return db.query(Clinic).filter(Clinic.id == clinic_id).first()

def get_doctor_by_id(db: Session, doctor_id: int) -> Optional[Doctor]:
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()

def create_doctor(db: Session, doctor_data: DoctorCreate) -> Doctor:
    new_doctor = Doctor(**doctor_data.model_dump())
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return new_doctor


def update_doctor(db: Session, doctor_id: int, doctor_update: DoctorUpdate) -> Optional[Doctor]:
    db_doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not db_doctor:
        return None
    
    update_data = doctor_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_doctor, key, value)
        
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

def delete_license(db: Session, license_id: int) -> bool:
    db_license = db.query(License).filter(License.id == license_id).first()
    if not db_license:
        return False
        
    db.delete(db_license)
    db.commit()
    return True

