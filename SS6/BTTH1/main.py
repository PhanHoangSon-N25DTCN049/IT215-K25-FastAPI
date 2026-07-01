from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field, field_validator
courses = [
    {"id": 1, "code": "PY101", "name": "Python Basic", "duration": 30, "fee": 3000000},
    {"id": 2, "code": "API101", "name": "FastAPI Basic", "duration": 24, "fee": 2500000},
    {"id": 3, "code": "JV101", "name": "Java Basic", "duration": 40, "fee": 4000000}
]

app = FastAPI()

class CreateCourse(BaseModel):
    code: str = Field(...)
    name: str = Field(...)
    duration: int = Field(..., gt=0)
    fee: int = Field(..., ge=0)
    
    @field_validator("name", "code")
    @classmethod
    def validate_name(cls, value: str, info):
        stripped = value.strip()
        if not stripped:
            raise ValueError(f"{info.field_name} must not be empty or whitespace")
        return stripped
    
@app.get("/courses", tags=["Courses"], status_code=status.HTTP_200_OK)
def get_courses(keyword: str | None = Query(default=None), min_fee: int | None = Query(default= None, ge=0), max_fee: int | None = Query(default= None, ge=0)):
    list_courses = courses
    if keyword is not None:
        list_courses = [c for c in list_courses if keyword.lower() in c["name"].lower() or keyword.lower() in c["code"].lower()]
        
    if min_fee is not None:
        list_courses = [c for c in list_courses if c["fee"] > min_fee]
        
    if max_fee is not None:
        list_courses = [c for c in list_courses if c["fee"] < max_fee]
        
    if not list_courses:
        return {
            "status":"success",
            "message":"Không tìm thấy môn học nào"
        }
    return {
        "status":"success",
        "message":"Danh sách khóa học được tìm thấy",
        "data":list_courses
    }
    
@app.get("/courses/{course_id}",status_code=status.HTTP_200_OK, tags=["Courses"])
def get_courses_by_id(course_id:int):
    course = next((c for c in courses if c["id"] == course_id),None)
    if course:
        return {
            "status":"success",
            "message":"Khóa học được tìm thấy",
            "data":course
        }
    raise HTTPException (
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Course not found"
    )
        

@app.post("/courses", status_code=status.HTTP_201_CREATED, tags=["Courses"])
def create_courses(course: CreateCourse):
    if any(c["code"] == course.code for c in courses):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Code môn học đã tồn tại"
        )
        
    new_id = max((c["id"] for c in courses), default=0) + 1
    new_course = {
        "id":new_id,
        "code": course.code,
        "name": course.name,
        "duration": course.duration,
        "fee": course.fee
    }
    courses.append(new_course)
    return {
        "status":"success",
        "message": "Tạo môn học mới thành công",
        "data": new_course
    }
    
@app.put("/courses/{course_id}", status_code=status.HTTP_200_OK, tags=["Courses"])
def update_course_by_id(course_id:int, course:CreateCourse):
    course_update = next((c for c in courses if c["id"] == course_id),None)
    if not course_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Course not found"
        )
    
    if any([c["code"] == course.code and c["id"] != course_id for c in courses]):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Code môn học đã tồn tại"
        )
    
    course_update.update(course.model_dump())
    return {"status": "success","message": "Cập nhật thành công", "data": course_update}

@app.delete("/courses/{course_id}", status_code=status.HTTP_200_OK, tags=["Courses"])
def del_course(course_id:int):
    course_del = next((c for c in courses if c["id"] == course_id),None)
    if not course_del:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Course not found"
        )
    courses.remove(course_del)
    return {
        "status" : "success",
        "message": "Xóa thành công"
    }