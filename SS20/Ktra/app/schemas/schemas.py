from pydantic import BaseModel, Field, EmailStr
from typing import Any
from fastapi import Request
from typing import List


class CreateEmployees(BaseModel):
    employee_code: str = Field(max_length=20, min_length=3)
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    department_id: int = Field(ge=1)

class CreateDepartments(BaseModel):
    department_code: str = Field(max_length=20, min_length=3)
    department_name: str = Field(min_length=2, max_length=100)


class DepartmentsData(BaseModel):
    id: int
    department_code: str
    department_name: str

    class Config:
        from_attributes = True

class EmployeesData(BaseModel):
    id: int
    employee_code: str
    full_name: str
    email: str
    department: DepartmentsData
    
    class Config:
            from_attributes = True
    
class DepartmentsResponse(BaseModel):
    statusCode: int
    message: str
    data: List["DepartmentsData"] | "DepartmentsData" | None = None
    error: str | None = None
    path: str
    
class EmployeesResponse(BaseModel):
    statusCode: int
    message: str
    data: List["EmployeesData"] | "EmployeesData" | None = None
    error: str | None = None
    path: str
    
def api_response(request: Request, statusCode: int, message: str, data: Any = None, error: str = None):
    return {
        "statusCode": statusCode,
        "message": message,
        "data": data,
        "error": error,
        "path": request.url.path
    }