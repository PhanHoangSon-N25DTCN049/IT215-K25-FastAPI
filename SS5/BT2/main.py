from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
app = FastAPI()
enrollments = [
    {
        "id": 1,
        "student_id": "SV001",
        "course_id": 1
    },
    {
        "id": 2,
        "student_id": "SV002",
        "course_id": 1
    }
]
class EnrollmentCreate(BaseModel):
    student_id: str
    course_id: int
    
@app.post("/enrollments", status_code=status.HTTP_201_CREATED)
def create_enrollment(enrollment: EnrollmentCreate):
    is_existed = any(
        e["student_id"] == enrollment.student_id and e["course_id"] == enrollment.course_id 
        for e in enrollments
    )
    
    if is_existed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sinh viên đã đăng ký khóa học này rồi"
        )
            
    new_enrollment = {
        "id": len(enrollments) + 1,
        "student_id": enrollment.student_id,
        "course_id": enrollment.course_id
    }
    enrollments.append(new_enrollment)
    
    return {
        "message": "Enroll successfully",
        "data": new_enrollment
    }