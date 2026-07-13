from sqlalchemy.orm import Session
from app.models.students import Students
from fastapi import status, HTTPException
def get_all(db: Session):
    return db.query(Students).all()

def get_by_class(db: Session, class_name: str = None):
    if class_name:
        return db.query(Students).filter(Students.class_name == class_name).all()
    return db.query(Students).all()

def get_by_id(db: Session, student_id: int):
    return db.query(Students).filter(Students.id == student_id).first()

def create(db: Session, student_data: dict):
    new_student = Students(**student_data)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

def update(db:Session, student_id: int ,student_data: dict):
    student = db.query(Students).filter(Students.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student Not Found")
    for key, value in student_data.items():
        setattr(student, key, value)
    
    db.commit()
    
    return student

def del_student(student_id: int, db:Session):
    student = db.query(Students).filter(Students.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student Not Found")
    db.delete(student)
    db.commit()
    
        