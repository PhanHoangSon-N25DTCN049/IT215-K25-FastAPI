from fastapi import FastAPI


students = [
    {"id": 1, "name": "An", "status": "active"},
    {"id": 2, "name": "Binh", "status": "inactive"},
    {"id": 3, "name": "Cuong", "status": "active"},
    {"id": 4, "name": "Dung", "status": "pending"}
]

app = FastAPI()

@app.get("/students/active")
def get_student_active():
    # list_student = [student for student in students if student["status"] == "active"]
    list_student = list(filter(lambda student: student["status"] == "active", students))
    if not list_student:
        return {
                    "message": "Không có sinh viên đang học",
                    "data": []
                }
    return {
        "message":"Danh sách sinh viên đang học",
        "data":list_student
    }

