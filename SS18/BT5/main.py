from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, String, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, Mapped, mapped_column, relationship

# Cấu hình Database
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/school_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    status: Mapped[str] = mapped_column(String(20)) # STUDYING, CANCELLED, COMPLETED

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")

Base.metadata.create_all(bind=engine)

# Schemas
class StudentDetail(BaseModel):
    id: int
    full_name: str
    email: str

class CourseStudentsResponse(BaseModel):
    course_id: int
    course_name: str
    total_students: int
    students: List[StudentDetail]

# App & API
app = FastAPI()

@app.get("/courses/{course_id}/students", response_model=CourseStudentsResponse)
def get_course_students(course_id: int, db: Session = Depends(get_db)):
    # 1. Kiểm tra khóa học có tồn tại không
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2. Xử lý truy vấn kết hợp (JOIN) để lấy danh sách sinh viên hợp lệ
    students_query = (
        db.query(Student)
        .join(Enrollment)
        .filter(
            Enrollment.course_id == course_id,
            Enrollment.status.in_(["STUDYING", "COMPLETED"]),
            Student.status == "ACTIVE"
        )
        .distinct()
        .order_by(Student.full_name.asc())
        .all()
    )

    # 3. Định dạng và trả về kết quả
    return CourseStudentsResponse(
        course_id=course.id,
        course_name=course.name,
        total_students=len(students_query),
        students=[
            StudentDetail(
                id=s.id,
                full_name=s.full_name,
                email=s.email
            ) for s in students_query
        ]
    )