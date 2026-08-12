from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
import enum

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/student_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class Classroom(Base):
    __tablename__ = "classrooms"
    id = Column(Integer, primary_key=True, index=True)
    class_code = Column(String(20), unique=True, index=True)
    class_name = Column(String(100))
    max_students = Column(Integer)
    status = Column(String(20), default="active")
    
    students = relationship("Student", back_populates="classroom")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String(20), unique=True, index=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    age = Column(Integer)
    gender = Column(Enum(GenderEnum))
    class_id = Column(Integer, ForeignKey("classrooms.id"))
    
    classroom = relationship("Classroom", back_populates="students")

Base.metadata.create_all(bind=engine)

class ClassroomOut(BaseModel):
    id: int
    class_code: str
    class_name: str
    class Config:
        from_attributes = True

class StudentCreateUpdate(BaseModel):
    student_code: str = Field(..., min_length=3, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=16, le=60)
    gender: GenderEnum
    class_id: int = Field(..., ge=1)

class StudentOut(BaseModel):
    id: int
    student_code: str
    full_name: str
    email: str
    age: int
    gender: str
    classroom: Optional[ClassroomOut]
    class Config:
        from_attributes = True

app = FastAPI()

def custom_response(status_code: int, message: str, request: Request, data: any = None, error: any = None):
    return {
        "statusCode": status_code,
        "message": message,
        "data": data if data is not None else {},
        "error": error,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "path": request.url.path
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=custom_response(422, "Dữ liệu không hợp lệ", request, error=exc.errors())
    )

@app.get("/students")
def get_list_students(request: Request, search: Optional[str] = None, class_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Student)
    
    if search:
        query = query.filter(
            (Student.full_name.contains(search)) | 
            (Student.student_code.contains(search)) | 
            (Student.email.contains(search))
        )
    if class_id:
        query = query.filter(Student.class_id == class_id)
        
    students = query.all()
    result = [StudentOut.model_validate(s).model_dump() for s in students]
    
    return custom_response(200, "Lấy danh sách thành công", request, data=result)

@app.get("/students/{student_id}")
def get_student_detail(student_id: int, request: Request, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return JSONResponse(
            status_code=404,
            content=custom_response(404, "Không tìm thấy sinh viên", request, error="Not Found")
        )
    return custom_response(200, "Thành công", request, data=StudentOut.model_validate(student).model_dump())

@app.post("/students", status_code=201)
def create_student(student: StudentCreateUpdate, request: Request, db: Session = Depends(get_db)):
    classroom = db.query(Classroom).filter(Classroom.id == student.class_id).first()
    if not classroom:
        return JSONResponse(status_code=400, content=custom_response(400, "Lớp học không tồn tại", request, error="Bad Request"))
    if classroom.status != "active":
        return JSONResponse(status_code=400, content=custom_response(400, "Lớp học không hoạt động", request, error="Bad Request"))
    
    current_students_count = db.query(Student).filter(Student.class_id == student.class_id).count()
    if current_students_count >= classroom.max_students:
        return JSONResponse(status_code=400, content=custom_response(400, "Lớp học đã đủ số lượng sinh viên", request, error="Bad Request"))
        
    if db.query(Student).filter(Student.student_code == student.student_code).first():
        return JSONResponse(status_code=400, content=custom_response(400, "Mã sinh viên đã tồn tại", request, error="Bad Request"))
    if db.query(Student).filter(Student.email == student.email).first():
        return JSONResponse(status_code=400, content=custom_response(400, "Email đã tồn tại", request, error="Bad Request"))

    new_student = Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    return custom_response(201, "Thêm sinh viên thành công", request, data=StudentOut.model_validate(new_student).model_dump())

@app.put("/students/{student_id}")
def update_student(student_id: int, student_update: StudentCreateUpdate, request: Request, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return JSONResponse(status_code=404, content=custom_response(404, "Không tìm thấy sinh viên", request, error="Not Found"))

    if db.query(Student).filter(Student.student_code == student_update.student_code, Student.id != student_id).first():
        return JSONResponse(status_code=400, content=custom_response(400, "Mã sinh viên bị trùng với sinh viên khác", request, error="Bad Request"))
    if db.query(Student).filter(Student.email == student_update.email, Student.id != student_id).first():
        return JSONResponse(status_code=400, content=custom_response(400, "Email bị trùng với sinh viên khác", request, error="Bad Request"))

    if student.class_id != student_update.class_id:
        new_class = db.query(Classroom).filter(Classroom.id == student_update.class_id).first()
        if not new_class:
            return JSONResponse(status_code=400, content=custom_response(400, "Lớp mới không tồn tại", request, error="Bad Request"))
        if new_class.status != "active":
            return JSONResponse(status_code=400, content=custom_response(400, "Lớp mới không hoạt động", request, error="Bad Request"))
        
        current_students_count = db.query(Student).filter(Student.class_id == student_update.class_id).count()
        if current_students_count >= new_class.max_students:
            return JSONResponse(status_code=400, content=custom_response(400, "Lớp mới đã đầy", request, error="Bad Request"))

    for key, value in student_update.model_dump().items():
        setattr(student, key, value)
        
    db.commit()
    db.refresh(student)
    
    return custom_response(200, "Cập nhật sinh viên thành công", request, data=StudentOut.model_validate(student).model_dump())