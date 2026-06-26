from fastapi import FastAPI

app = FastAPI(
    title="Course Management API",
    description="API quản lý hệ thống khóa học dành cho sinh viên",
    version="1.0.0"
)



@app.get("/courses")
def get_all_courses():
    """Lấy danh sách tất cả các khóa học trong hệ thống"""
    return {
        "status": "success",
        "message": "Lấy danh sách khóa học thành công",
        "data": [
            {"id": 1, "title": "FastAPI Cơ Bản", "category": "Backend"},
            {"id": 2, "title": "Next.js Nâng Cao", "category": "Frontend"}
        ]
    }

@app.get("/courses/detail")
def get_course_detail():
    """Xem thông tin chi tiết của một khóa học cụ thể"""
    return {
        "status": "success",
        "message": "Lấy thông tin chi tiết khóa học thành công",
        "data": {
            "id": 1,
            "title": "FastAPI Cơ Bản",
            "duration": "15 buổi",
            "instructor": "Vampire Mentor"
        }
    }

@app.post("/courses")
def create_course():
    """Thêm mới một khóa học vào hệ thống"""
    return {
        "status": "success",
        "message": "Thêm mới khóa học thành công"
    }

@app.put("/courses/update")
def update_course():
    """Cập nhật thông tin của khóa học hiện tại"""
    return {
        "status": "success",
        "message": "Cập nhật thông tin khóa học thành công"
    }

@app.delete("/courses/delete")
def delete_course():
    """Xóa một khóa học ra khỏi hệ thống"""
    return {
        "status": "success",
        "message": "Xóa khóa học thành công"
    }

@app.get("/courses/statistics")
def get_courses_statistics():
    """Xem số liệu thống kê tổng quan về hệ thống khóa học"""
    return {
        "status": "success",
        "message": "Lấy dữ liệu thống kê thành công",
        "data": {
            "total_courses": 42,
            "active_students": 150,
            "completed_rate": "85%"
        }
    }

@app.get("/courses/free")
def get_free_courses():
    """Lọc nhanh danh sách các khóa học miễn phí (0đ) cho sinh viên"""
    return {
        "status": "success",
        "message": "Lấy danh sách khóa học miễn phí thành công",
        "data": [
            {"id": 3, "title": "Git & GitHub cho người mới bắt đầu", "price": 0}
        ]
    }

@app.get("/courses/trending")
def get_trending_courses():
    """Lấy danh sách khóa học hot nhất, có số lượt đăng ký nhiều nhất tuần"""
    return {
        "status": "success",
        "message": "Lấy danh sách khóa học thịnh hành thành công",
        "data": [
            {"id": 1, "title": "FastAPI Cơ Bản", "views": 2500}
        ]
    }