from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# --- SCHEMAS FOR DOCTOR ---
class DoctorBase(BaseModel):
    doctor_code: str
    salary: float
    clinic_id: int

class DoctorDetail(DoctorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DoctorUpdate(BaseModel):
    doctor_code: Optional[str] = None
    salary: Optional[float] = None
    clinic_id: Optional[int] = None

# --- SCHEMAS FOR CLINIC ---
class ClinicCreate(BaseModel):
    clinic_name: str
    specialty: str

class ClinicDetailResponse(ClinicCreate):
    id: int
    # Lồng ghép danh sách bác sĩ thuộc phòng khám
    doctors: List[DoctorDetail] = []
    model_config = ConfigDict(from_attributes=True)

# --- SCHEMAS FOR LICENSE ---
class LicenseResponse(BaseModel):
    id: int
    license_number: str
    issue_by: str
    doctor_id: int
    model_config = ConfigDict(from_attributes=True)