from fastapi import FastAPI

"""
Dưới đây là phần giải thích ngắn gọn, tự nhiên theo đúng kiểu sinh viên nói chuyện với nhau để bạn nắm rõ vấn đề của bài tập:

### 1. Tại sao API bị lỗi hiển thị?
Bình thường khi làm API với FastAPI, nếu mình trả về một danh sách (list) hay một dictionary,
thằng FastAPI nó sẽ tự động chuyển dữ liệu đó thành định dạng JSON chuẩn chỉnh để frontend đọc được luôn.
Nhưng ở đây, code cũ lại dùng cách cộng chuỗi thủ công (string concatenation) để gom danh sách sinh viên thành một chuỗi văn bản dài. Khi trả về một cái `string` như vậy,
FastAPI sẽ gửi nó đi dưới dạng text thuần túy (`text/plain`). Hệ quả là bên frontend khi gọi hàm `response.json()`
sẽ bị lỗi ngay lập tức vì nó nhận về một cục chữ liền nhau chứ không phải một mảng (Array) để mà dùng vòng lặp duyệt qua từng sinh viên rồi render lên giao diện.
### 2. Lỗi đặt tên endpoint (Naming Convention)
Cái endpoint cũ đang đặt tên là `/getStudents`. Trong thiết kế chuẩn RESTful API,
người ta quy ước đường dẫn (endpoint) chỉ được dùng **danh từ** (thường là số nhiều) để đại diện cho tài nguyên hệ thống,
còn hành động thì để cho các phương thức HTTP (HTTP Methods) lo.
Ở đây, mình đang muốn "lấy" dữ liệu thì đã dùng phương thức `GET` rồi, việc nhét thêm chữ `get` vào đường dẫn `/getStudents` vừa bị thừa thãi, vừa sai quy chuẩn thiết kế.

---

### 3. Hướng giải quyết

* **Sửa lại endpoint:** Đổi hành vi gọi từ `GET /getStudents` thành `GET /students` cho đúng chuẩn RESTful.
* **Sửa lại dữ liệu trả về:** Thay vì cộng chuỗi, mình tạo một danh sách các dictionary (hoặc lấy từ database dạng list) rồi `return` trực tiếp cái list đó. FastAPI sẽ tự lo phần ép về JSON array chuẩn cho frontend húp trọn dữ liệu.
"""




app = FastAPI()

students_db = [
    {"id": 1, "name": "Nguyen Van A", "class": "HNKS25CNTT1"},
    {"id": 2, "name": "Tran Thi B", "class": "HNKS25CNTT1"},
    {"id": 3, "name": "Le Van C", "class": "HNKS25CNTT1"}
]

@app.get("/students")
def get_all_students():
    return students_db