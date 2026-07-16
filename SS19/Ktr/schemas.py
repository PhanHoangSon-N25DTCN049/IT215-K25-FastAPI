from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ClinicCreate(BaseModel):
    clinic_name: str
    specialty: str

class DoctorCreate(BaseModel):
    doctor_code: str
    salary: float
    clinic_id: int

class DoctorUpdate(BaseModel):
    doctor_code: Optional[str] = None
    salary: Optional[float] = None
    clinic_id: Optional[int] = None

class ClinicResponse(BaseModel):
    id: int
    clinic_name: str 
    specialty: str
    
    
    model_config = ConfigDict(from_attributes=True)

class LicenseResponse(BaseModel): 
    id: int 
    license_number: str 
    issue_by: str 
    doctor_id: int
    
    model_config = ConfigDict(from_attributes=True)

class DoctorResponseForClinic(BaseModel):
    id: int 
    doctor_code: str
    salary: float
    license: Optional[LicenseResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

class DoctorResponse(BaseModel):
    id: int 
    doctor_code: str
    salary: float
    clinic: ClinicResponse
    license: Optional[LicenseResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

class ClinicDetailResponse(ClinicResponse):
    doctors: List[DoctorResponseForClinic]  
    
    model_config = ConfigDict(from_attributes=True)