from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field, field_validator

students = [
    {"id": 1, "code": "SV001", "name": "Nguyen Van A", "email": "a@gmail.com", "age": 20},
    {"id": 2, "code": "SV002", "name": "Tran Thi B", "email": "b@gmail.com", "age": 22},
    {"id": 3, "code": "SV003", "name": "Le Van C", "email": "c@gmail.com", "age": 18}
]


app = FastAPI()

class RequestStudent(BaseModel):
    code : str 
    name : str 
    email : str 
    age : int = Field(gt=0)

    @field_validator("name" , "code", "email")
    @classmethod
    def validate_string(cls, value:str, info):
        temp = value.strip()
        if not temp:
            raise ValueError(f"{info.field_name} Không được bỏ trống")
        return temp

@app.get("/students")
def get_student(keyword: str | None = None, min_age:int | None = Query(default= None, gt=0), max_age: int | None = Query(default= None, gt=0)):
    list_student = students
    if keyword:
        list_student = [s for s in list_student if keyword.lower() in s["name"].lower() or keyword.lower() in s["code"].lower() or keyword.lower() in s["email"].lower()]
    
    if min_age:
        list_student = [s for s in list_student if s["age"] >= min_age]
    
    if max_age:
        list_student = [s for s in list_student if s["age"] <= max_age]
        
    return {
        "status": "success",
        "message": "danh sách học sinh tìm thấy",
        "data":list_student
    }

@app.get("/students/{student_id}")
def get_student_by_id(student_id:int):
    student = next((s for s in students if student_id == s["id"]), None)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {
        "status":"success",
        "message":"Thông tin sinh viên tìm thấy",
        "data":student
    }
    
@app.post("/students")
def create_student(student: RequestStudent):
    if any(s["code"] == student.code for s in students):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mã học sinh đã tồn tại")
    
    new_student = {
        "id": max((s["id"] for s in students), default=0) + 1,
        "code": student.code,
        "name":student.name,
        "email":student.email,
        "age":student.age
    }
    students.append(new_student)
    return {
        "status": "success",
        "message": "Thêm sinh viên thành công",
        "data": new_student
    }
    
@app.put("/students/{student_id}")
def update_student(student_id:int, student: RequestStudent):
    student_update = next((s for s in students if student_id == s["id"]), None)
    if not student_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sinh viên không tồn tại")
    
    if any(s["code"] == student.code and s["id"] != student_id for s in students):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ID được cập nhật đã tồn tại")
    
    student_update.update(student.model_dump())
    return {
        "status":"success",
        "message":"Cập nhật thông tin sinh viên thành công",
        "data": student_update
    }
    
@app.delete("/students/{student_id}")
def del_student(student_id:int):
    student = next((s for s in students if student_id == s["id"]), None)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sinh viên không tồn tại")
    
    students.remove(student)
    return {
        "status":"success",
        "message":"Xóa sinh viên thành công"
    }