from fastapi import FastAPI

""" 
endpoint hiện tại là /student
khi gọi /students sẽ bị lỗi 404 Not Found do endpoint đang là /student
tên endpoint /student chưa phù hợp với yêu cầu lấy danh sách sinh viên vì đây là số ít phải thêm s thành /students để đúng chuẩn
dòng return students[0] chưa đúng với yêu cầu nghiệp vụ vì chỉ trả về sinh viên đầu tiên trong danh sách
API đúng theo yêu cầu khách hàng nên có đường dẫn là /students 

"""

from fastapi import FastAPI

app = FastAPI()
students = [
    {"id": 1, "name": "An"},
    {"id": 2, "name": "Binh"},
    {"id": 3, "name": "Cuong"},
]

@app.get("/students")
def get_student():
    return students