from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import string
import random

app = FastAPI()

class StudentRegister(BaseModel):
    full_name: str = Field(..., min_length=3, description="Họ tên tối thiểu 3 ký tự")
    email: EmailStr = Field(..., description="Phải đúng định dạng gmail")
    age: int = Field(..., ge=15, le=60, description="Tuổi từ 15 đến 60")
    phone: str = Field(..., min_length=10, max_length=11, pattern=r'^\d+$', description="Số điện thoại từ 10 -> 11 số")
    note: Optional[str] = Field(default= None, max_length=200, description="Tối đa 200 ký tự")
    
    @field_validator('full_name')
    @classmethod
    def normalize_name(cls,value: str):
        return value.strip().title()
    

@app.post("/students/register")
def post_register(student: StudentRegister):
    student_id = "HV"+"".join(random.choices(string.digits, k=5))
    response_data = student.model_dump(exclude_none= True)
    response_data["student_id"] = student_id
    return {
        "message": "Đăng ký học viên thành công",
        "data": response_data
    }