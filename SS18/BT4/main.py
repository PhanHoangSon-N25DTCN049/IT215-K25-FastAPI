from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine, String, ForeignKey, Integer, CheckConstraint, DateTime, func, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, Session, Mapped, mapped_column, relationship

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/workshop_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Student(Base):
    __tablename__ = "students"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    
    registration: Mapped[list["Registration"]] = relationship(back_populates="student")
    
class Workshop(Base):
    __tablename__ = "workshop"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    maximum_participants: Mapped[int] = mapped_column(Integer, CheckConstraint("maximum_participants > 0"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    
    registration: Mapped[list["Registration"]] = relationship(back_populates="workshop")
    
class Registration(Base):
    __tablename__ = "registration"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshop.id"))
    registered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="REGISTERED")

    student: Mapped["Student"] = relationship(back_populates="registration")
    workshop: Mapped["Workshop"] = relationship(back_populates="registration")
    
    __table_args__ = (
        UniqueConstraint("student_id", "workshop_id", name="uix_student_workshop"),  
    )

Base.metadata.create_all(bind=engine)

class StudentCreate(BaseModel):
    student_code: str
    full_name: str
    email: EmailStr
    status: Optional[str] = "ACTIVE"

class StudentResponse(StudentCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class WorkshopCreate(BaseModel):
    title: str
    description: str
    maximum_participants: int
    status: Optional[str] = "OPEN"
    start_time: Optional[datetime] = None

class WorkshopResponse(WorkshopCreate):
    id: int
    start_time: datetime
    model_config = ConfigDict(from_attributes=True)

class RegistrationCreate(BaseModel):
    student_id: int
    workshop_id: int

class RegistrationResponse(BaseModel):
    id: int
    student_id: int
    workshop_id: int
    registered_at: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)

app = FastAPI(title="Workshop Registration System")

@app.post("/students", response_model=StudentResponse, status_code=201)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(
        (Student.email == student.email) | (Student.student_code == student.student_code)
    ).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Mã sinh viên hoặc Email đã tồn tại.")
    
    new_student = Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students", response_model=List[StudentResponse])
def get_students(db: Session = Depends(get_db)):
    return db.query(Student).all()

@app.post("/workshops", response_model=WorkshopResponse, status_code=201)
def create_workshop(workshop: WorkshopCreate, db: Session = Depends(get_db)):
    if workshop.maximum_participants <= 0:
        raise HTTPException(status_code=400, detail="Số lượng tham gia tối đa phải lớn hơn 0.")
        
    workshop_data = workshop.model_dump(exclude_unset=True)
    if 'start_time' not in workshop_data or workshop_data['start_time'] is None:
        workshop_data['start_time'] = datetime.now()
        
    new_workshop = Workshop(**workshop_data)
    db.add(new_workshop)
    db.commit()
    db.refresh(new_workshop)
    return new_workshop

@app.get("/workshops", response_model=List[WorkshopResponse])
def get_workshops(db: Session = Depends(get_db)):
    return db.query(Workshop).all()

@app.get("/workshops/{id}", response_model=WorkshopResponse)
def get_workshop_detail(id: int, db: Session = Depends(get_db)):
    workshop = db.query(Workshop).filter(Workshop.id == id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Không tìm thấy workshop.")
    return workshop

@app.post("/registrations", response_model=RegistrationResponse, status_code=201)
def register_workshop(reg: RegistrationCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == reg.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại.")
    if student.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Sinh viên không ở trạng thái hoạt động.")
        
    workshop = db.query(Workshop).filter(Workshop.id == reg.workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop không tồn tại.")
    if workshop.status != "OPEN":
        raise HTTPException(status_code=400, detail="Workshop đã đóng đăng ký.")
        
    existing_reg = db.query(Registration).filter(
        Registration.student_id == reg.student_id,
        Registration.workshop_id == reg.workshop_id,
        Registration.status == "REGISTERED"
    ).first()
    if existing_reg:
        raise HTTPException(status_code=400, detail="Sinh viên đã đăng ký workshop này rồi.")
        
    current_participants = db.query(Registration).filter(
        Registration.workshop_id == reg.workshop_id,
        Registration.status == "REGISTERED"
    ).count()
    if current_participants >= workshop.maximum_participants:
        raise HTTPException(status_code=400, detail="Workshop đã đủ số lượng đăng ký.")

    cancelled_reg = db.query(Registration).filter(
        Registration.student_id == reg.student_id,
        Registration.workshop_id == reg.workshop_id,
        Registration.status == "CANCELLED"
    ).first()
    
    if cancelled_reg:
        cancelled_reg.status = "REGISTERED"
        cancelled_reg.registered_at = datetime.now()
        db.commit()
        db.refresh(cancelled_reg)
        return cancelled_reg
    else:
        new_reg = Registration(student_id=reg.student_id, workshop_id=reg.workshop_id)
        db.add(new_reg)
        db.commit()
        db.refresh(new_reg)
        return new_reg

@app.get("/students/{id}/workshops", response_model=List[WorkshopResponse])
def get_student_workshops(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Sinh viên không tồn tại.")
        
    workshops = db.query(Workshop).join(Registration).filter(
        Registration.student_id == id,
        Registration.status == "REGISTERED"
    ).all()
    return workshops

@app.get("/workshops/{id}/students", response_model=List[StudentResponse])
def get_workshop_students(id: int, db: Session = Depends(get_db)):
    workshop = db.query(Workshop).filter(Workshop.id == id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop không tồn tại.")
        
    students = db.query(Student).join(Registration).filter(
        Registration.workshop_id == id,
        Registration.status == "REGISTERED"
    ).all()
    return students

@app.put("/registrations/{id}")
def cancel_registration(id: int, db: Session = Depends(get_db)):
    registration = db.query(Registration).filter(Registration.id == id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Bản ghi đăng ký không tồn tại.")
        
    if registration.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Đăng ký này đã được hủy trước đó.")
        
    registration.status = "CANCELLED"
    db.commit()
    return {"message": "Hủy đăng ký thành công.", "registration_id": id}