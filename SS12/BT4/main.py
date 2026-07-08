from fastapi import FastAPI, status, HTTPException, Depends
from sqlalchemy import text, create_engine, String
from sqlalchemy.orm import Session, sessionmaker, declarative_base, Mapped, mapped_column
from pydantic import BaseModel
app = FastAPI()

DATABASE_URL = "sqlite:///./homeword.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
class Students(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

Base.metadata.create_all(engine)


class StudentCreate(BaseModel):
    full_name: str
    email: str
        
@app.get("/database/health", status_code=status.HTTP_200_OK, tags=["Database"])
def get_health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        
        return {
            "message": f"Lỗi kết nối database{e}"
        }
    else:
        return {
            "message": "Kết nối database thành công"
        }


@app.get("/students")
def get_student(db:Session = Depends(get_db)):
    try:
        list_Student = db.query(Students).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail= f"Lỗi lấy dữ liệu database {e}"
        )
    else:
        return {
            "data": list_Student
        }

@app.post("/students")
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    try:
        new_student = Students(**student.model_dump())
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
    except Exception as e:
        return {
            "message": f"Lỗi tạo dữ liệu {e}"
        }
    else:
        return {
            "message": "tạo dữ liệu thành công"
        }

# Xóa student 
@app.delete("/students/{student_id}")
def del_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Students).filter(Students.id == student_id).first()
    if not student:
        raise HTTPException (
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Học viên không tồn tại trong hệ thống"
        ) 
    try:
        db.delete(student)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException (
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi Xóa dữ liệu {e}"
        )
    else:
        return {
            "message":"Xóa dữ liệu thành công",
            "data": student
        }