from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy import Integer, String, DateTime, ForeignKey, create_engine, select, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import enum

# ==========================================
# 1. DATABASE CONFIG & MODELS
# ==========================================
DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/workshop_db" 
engine = create_engine(DATABASE_URL)

class Base(DeclarativeBase):
    pass

class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class WorkshopStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class RegStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    CANCELLED = "CANCELLED"

class Student(Base):
    __tablename__ = "student"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[StudentStatus] = mapped_column(String(50), default=StudentStatus.ACTIVE)
    
    registrations: Mapped[list["Registration"]] = relationship(back_populates="student")

class Workshop(Base):
    __tablename__ = "workshop"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    maximum_participants: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[WorkshopStatus] = mapped_column(String(50), default=WorkshopStatus.OPEN)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    registrations: Mapped[list["Registration"]] = relationship(back_populates="workshop")

class Registration(Base):
    __tablename__ = "registration"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshop.id"))
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[RegStatus] = mapped_column(String(50), default=RegStatus.REGISTERED)
    
    student: Mapped["Student"] = relationship(back_populates="registrations")
    workshop: Mapped["Workshop"] = relationship(back_populates="registrations")

# Tạo bảng
Base.metadata.create_all(bind=engine)

def get_db():
    with Session(engine) as session:
        yield session


class StudentCreate(BaseModel):
    student_code: str
    full_name: str
    email: str

class StudentOut(StudentCreate):
    id: int
    status: StudentStatus

class WorkshopCreate(BaseModel):
    title: str
    description: Optional[str] = None
    maximum_participants: int
    start_time: datetime

class WorkshopOut(WorkshopCreate):
    id: int
    status: WorkshopStatus

class RegistrationCreate(BaseModel):
    student_id: int
    workshop_id: int

class RegistrationOut(BaseModel):
    id: int
    student_id: int
    workshop_id: int
    registered_at: datetime
    status: RegStatus

app = FastAPI(title="Workshop Registration System")

@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    # Check email hoặc code trùng lặp có thể xử lý thêm ở đây
    new_student = Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students", response_model=List[StudentOut])
def get_students(db: Session = Depends(get_db)):
    return db.scalars(select(Student)).all()

@app.post("/workshops", response_model=WorkshopOut, status_code=status.HTTP_201_CREATED)
def create_workshop(workshop: WorkshopCreate, db: Session = Depends(get_db)):
    new_workshop = Workshop(**workshop.model_dump())
    db.add(new_workshop)
    db.commit()
    db.refresh(new_workshop)
    return new_workshop

@app.get("/workshops", response_model=List[WorkshopOut])
def get_workshops(db: Session = Depends(get_db)):
    return db.scalars(select(Workshop)).all()

@app.get("/workshops/{id}", response_model=WorkshopOut)
def get_workshop_detail(id: int, db: Session = Depends(get_db)):
    workshop = db.get(Workshop, id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop không tồn tại")
    return workshop

@app.post("/registrations", response_model=RegistrationOut, status_code=status.HTTP_201_CREATED)
def register_workshop(reg_in: RegistrationCreate, db: Session = Depends(get_db)):
    student = db.get(Student, reg_in.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại")
    if student.status != StudentStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Tài khoản sinh viên không hoạt động")

    workshop = db.get(Workshop, reg_in.workshop_id)
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop không tồn tại")
    if workshop.status != WorkshopStatus.OPEN:
        raise HTTPException(status_code=400, detail="Workshop đã đóng hoặc bị hủy")

    existing_reg = db.scalar(
        select(Registration).where(
            Registration.student_id == reg_in.student_id,
            Registration.workshop_id == reg_in.workshop_id,
            Registration.status == RegStatus.REGISTERED
        )
    )
    if existing_reg:
        raise HTTPException(status_code=400, detail="Sinh viên đã đăng ký workshop này")

    current_participants = db.scalar(
        select(func.count(Registration.id)).where(
            Registration.workshop_id == reg_in.workshop_id,
            Registration.status == RegStatus.REGISTERED
        )
    )
    if current_participants >= workshop.maximum_participants:
        raise HTTPException(status_code=400, detail="Workshop đã đủ số lượng người đăng ký")

    new_reg = Registration(student_id=reg_in.student_id, workshop_id=reg_in.workshop_id)
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return new_reg

@app.put("/registrations/{id}", response_model=RegistrationOut)
def cancel_registration(id: int, db: Session = Depends(get_db)):
    registration = db.get(Registration, id)
    if not registration:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin đăng ký")
    if registration.status == RegStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Đăng ký này đã được hủy trước đó")
    
    registration.status = RegStatus.CANCELLED
    db.commit()
    db.refresh(registration)
    return registration

@app.get("/students/{id}/workshops", response_model=List[WorkshopOut])
def get_student_workshops(id: int, db: Session = Depends(get_db)):
    stmt = (
        select(Workshop)
        .join(Registration, Workshop.id == Registration.workshop_id)
        .where(
            Registration.student_id == id,
            Registration.status == RegStatus.REGISTERED
        )
    )
    return db.scalars(stmt).all()

@app.get("/workshops/{id}/students", response_model=List[StudentOut])
def get_workshop_students(id: int, db: Session = Depends(get_db)):
    stmt = (
        select(Student)
        .join(Registration, Student.id == Registration.student_id)
        .where(
            Registration.workshop_id == id,
            Registration.status == RegStatus.REGISTERED
        )
    )
    return db.scalars(stmt).all()