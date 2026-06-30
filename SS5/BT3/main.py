from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

students = [{"id": 1, "name": "Nguyen Van A"}, {"id": 2, "name": "Tran Thi B"}, {"id": 3, "name": "Le Van C"}]
courses = [{"id": 1, "name": "FastAPI Basic", "capacity": 2}, {"id": 2, "name": "Python OOP", "capacity": 2}]
registrations = [{"id": 1, "student_id": 1, "course_id": 1}, {"id": 2, "student_id": 2, "course_id": 1}]

class RegistrationCreate(BaseModel):
    student_id: int
    course_id: int

@app.post("/registrations", status_code=status.HTTP_201_CREATED)
def create_registration(reg: RegistrationCreate):
    student = next((s for s in students if s["id"] == reg.student_id), None)
    course = next((c for c in courses if c["id"] == reg.course_id), None)
    if not student or not course:
        raise HTTPException(status_code=404, detail="Student or Course not found")

    if any(r["student_id"] == reg.student_id and r["course_id"] == reg.course_id for r in registrations):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already registered this course")

    enrolled_count = len([r for r in registrations if r["course_id"] == reg.course_id])
    if enrolled_count >= course["capacity"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Course is full")

    new_reg = {
        "id": len(registrations) + 1,
        "student_id": reg.student_id,
        "course_id": reg.course_id
    }
    registrations.append(new_reg)
    return {"message": "Create successfully", "data": new_reg}