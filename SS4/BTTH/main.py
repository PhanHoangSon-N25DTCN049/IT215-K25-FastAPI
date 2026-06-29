from fastapi import FastAPI, Query

courses = [
    {
        "id": 1,
        "name": "Python Basic",
        "category": "backend",
        "price": 3000000,
        "mode": "online"
    },
    {
        "id": 2,
        "name": "Java Web",
        "category": "backend",
        "price": 5000000,
        "mode": "offline"
    },
    {
        "id": 3,
        "name": "Web Frontend",
        "category": "frontend",
        "price": 4000000,
        "mode": "online"
    }
]
app = FastAPI()

@app.get("/courses")
def get_courses():
    return {
        "message": "Lấy danh sách khóa học thành công",
        "data": courses
    }

@app.get("/courses/search")
def get_courses_search(mode: str | None = Query(default=None), category: str | None = Query(default=None)):
    list_return = courses
    if mode is not None:
        list_return = [course for course in list_return if course["mode"] == mode]
    if category is not None:
        list_return = [course for course in list_return if course["category"] == category]
    if not list_return:
        return {
            "message":"Không tìm thấy khóa học đáp ưng"
        }
    return {
        "message": "Danh sách khóa học tìm thấy",
        "data": list_return
    }
    
@app.get("/courses/{course_id}")
def get_course_id(course_id:int):
    course_return = []
    for course in courses:
        if course["id"] == course_id:
            course_return = course
            break
        
    if not course_return:
        return{
            "message": "Không tìm thấy khóa học"
        }
    return {
            "message": "Tìm thấy khóa học",
            "data": course_return
            }