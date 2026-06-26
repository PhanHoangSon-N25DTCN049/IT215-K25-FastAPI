from fastapi import FastAPI

courses = [
    {
        "id": 1,
        "code": "PY101",
        "name": "Python Basic",
        "level": "beginner",
        "price": 1500000
    },
    {
        "id": 2,
        "code": "FA101",
        "name": "FastAPI Basic",
        "level": "beginner",
        "price": 2000000
    }
]

app = FastAPI()

@app.get("/health")
def get_health():
    return{
        "message": "API is running"
    }

@app.get("/courses")
def get_courses():
    return {
        "message":"Toàn bộ danh sách khóa học",
        "data": courses
    }
    
@app.get("/courses/{course_id}")
def get_courses(course_id: int):
    get_course = None
    if course_id <= 0:
        return {
            "status": 404,
            "error": "Not Found",
            "message": f"id khóa học không nhỏ hơn hoặc bằng 0",
        }
    for course in courses:
        if course["id"] == course_id:
            get_course = course
            break
            
    if get_course == None:
        return {
            "status": 404,
            "error": "Not Found",
            "message": f"Không tìm thấy khóa học với ID {course_id}",
        }
    return {
        "message":"Thông tin khóa học",
        "data": get_course
    }