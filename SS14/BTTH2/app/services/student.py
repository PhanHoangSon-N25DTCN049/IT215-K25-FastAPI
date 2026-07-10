from sqlalchemy.orm import Session
from app.models.student import Students

def get_all(db: Session):
    return db.query(Students).all()

def get_by_id(student_id: int, db: Session):
    return db.query(Students).filter(Students.id == student_id).first()

def create(student_data:dict, db: Session):
    db_student = Students(**student_data)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def update(student_data: dict,db_student: Students, db: Session):
    for key, value in student_data.items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student

def del_student(db_student: Students, db: Session):
    db.delete(db_student)
    db.commit()
    