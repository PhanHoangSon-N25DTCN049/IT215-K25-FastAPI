from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

app = FastAPI()

# Giả lập cơ sở dữ liệu (Database mock)
students_db = [
    {
        "full_name": "Nguyen Van A",
        "email": "existing@gmail.com",
        "age": 20,
        "course": "python",
        "phone": "0987654321"
    }
]

# Định nghĩa Schema để nhận và Validate dữ liệu từ request body
class StudentCreate(BaseModel):
    # Quy tắc 1: Bắt buộc, không để trống, tối thiểu 3 ký tự
    full_name: str = Field(..., min_length=3, description="Họ tên học viên")
    # Quy tắc 2 & Bẫy 1, 2: Bắt buộc, tự động kiểm tra chuẩn định dạng email
    email: EmailStr 
    age: int
    course: str
    phone: str

@app.post("/students")
def create_student(student: StudentCreate):
    # Bẫy 3: Xử lý email đã tồn tại trong hệ thống
    for existing_student in students_db:
        if existing_student["email"] == student.email:
            raise HTTPException(
                status_code=400, 
                detail="Email đã tồn tại trong hệ thống"
            )
    
    # Nếu không vướng bẫy, tiến hành lưu vào DB
    new_student = student.model_dump() # Pydantic v2 (dùng .dict() nếu ở Pydantic v1)
    students_db.append(new_student)
    
    return {
        "message": "Thêm học viên thành công",
        "data": new_student
    }