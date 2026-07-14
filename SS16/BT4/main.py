from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy import Integer, String, ForeignKey, select
from pydantic import BaseModel

app = FastAPI()

class Base(DeclarativeBase):
    pass

class Course(Base):
    __tablename__ = "course"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")

class Student(Base):
    __tablename__ = "student"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50))
    
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")

class Enrollment(Base):
    __tablename__ = "enrollment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"))
    status: Mapped[str] = mapped_column(String(50))
    
    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")

class StudentResponse(BaseModel):
    id: int
    full_name: str
    email: str

class CourseStudentsResponse(BaseModel):
    course_id: int
    course_name: str
    total_students: int
    students: list[StudentResponse]

def get_db():
    pass

@app.get("/courses/{course_id}/students", response_model=CourseStudentsResponse)
def get_course_students(course_id: int, db: Session = Depends(get_db)):
    
    course = db.scalars(select(Course).where(Course.id == course_id)).first()
    if not course:
        raise HTTPException(status_code=404, detail="Khóa học không tồn tại")

    stmt = (
        select(Student)
        .join(Enrollment, Student.id == Enrollment.student_id)
        .where(
            Enrollment.course_id == course_id,
            Enrollment.status.in_(["STUDYING", "COMPLETED"]),
            Student.status == "ACTIVE"
        )
        .distinct()
        .order_by(Student.full_name.asc())
    )
    
    students = db.scalars(stmt).all()

    return {
        "course_id": course.id,
        "course_name": course.name,
        "total_students": len(students),
        "students": [
            {
                "id": s.id, 
                "full_name": s.full_name, 
                "email": s.email
            } for s in students
        ]
    }