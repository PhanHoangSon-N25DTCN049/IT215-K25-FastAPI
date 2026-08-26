# 🚀 FastAPI Project & Task Management API (IT215)

RESTful API Backend cho hệ thống Quản lý Dự án và Công việc (Project & Task Management) được xây dựng bằng **FastAPI**, **SQLAlchemy ORM** và **MySQL**.

---

## 📌 Các Tính Năng Chính
- 🔐 **Authentication & Authorization**: Đăng ký, đăng nhập JWT Access/Refresh Token, phân quyền `ADMIN` và `USER`, Rate Limiting bảo vệ API.
- 📁 **Project Management**: Tạo, cập nhật, xóa mềm dự án, thêm/xóa thành viên và phân quyền (`OWNER`, `MEMBER`).
- ✅ **Task Management**: Quản lý công việc với đầy đủ trạng thái (`TODO`, `IN_PROGRESS`, `DONE`), độ ưu tiên (`LOW`, `MEDIUM`, `HIGH`), deadline và người phụ trách.
- 💬 **Task Comments**: Thảo luận và trao đổi công việc theo từng task.
- 📜 **Activity Logs**: Tự động ghi lại lịch sử các thao tác quan trọng trên dự án.

---

## 🛠️ Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Kích hoạt môi trường ảo & cài đặt thư viện
```bash
# Kích hoạt venv trên Windows
.\venv\Scripts\activate

# Cài đặt thư viện phụ thuộc (nếu cần)
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Kiểm tra file `.env` tại thư mục gốc:
```env
DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/project_fastapi_db"
SECRET_KEY = "x9J2@L$v8Bw#p7Z!m5Y*3kP&1Nq4R6X8wZ9J2@L$v8Bw#p7Z!m5Y*3kP&1Nq4R6X"
REFRESH_SECRET_KEY = "f8a2b5c7e1d4908f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f"
```

### 3. Nạp dữ liệu mẫu (Seed Data)
Chạy script `seed_data.py` để nạp dữ liệu mẫu hoàn chỉnh:
```bash
# Nạp dữ liệu mẫu mới (giữ dữ liệu hiện tại)
python seed_data.py

# Hoặc xóa sạch và nạp lại toàn bộ dữ liệu mẫu từ đầu:
python seed_data.py --reset
```

### 4. Khởi chạy Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- **API Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 5. Chạy Automated Tests
```bash
python -m pytest -v
```

---

## 👥 Danh Sách Tài Khoản Mẫu (Seed Accounts)

> 🔑 **Mật khẩu chung cho tất cả các tài khoản**: `Password123@`

| Email | Họ và Tên | Vai trò | Trạng thái |
| :--- | :--- | :---: | :---: |
| `admin@fastapi.dev` | Quản Trị Viên Hệ Thống | `ADMIN` | Hoạt động |
| `son.phan@example.com` | Phan Hoàng Sơn | `USER` | Hoạt động |
| `lan.nguyen@example.com` | Nguyễn Thị Mai Lan | `USER` | Hoạt động |
| `nam.tran@example.com` | Trần Văn Nam | `USER` | Hoạt động |
| `huong.le@example.com` | Lê Thu Hương | `USER` | Hoạt động |
| `minh.vu@example.com` | Vũ Tuấn Minh | `USER` | Hoạt động |
| `duc.hoang@example.com` | Hoàng Minh Đức | `USER` | Hoạt động |
| `trang.do@example.com` | Đỗ Quỳnh Trang | `USER` | Hoạt động |
| `khoa.dang@example.com` | Đặng Anh Khoa | `USER` | **Đã khóa (Test Inactive)** |
| `user1@example.com` | Người Dùng Mẫu 1 | `ADMIN` | Hoạt động |
| `user2@example.com` | Người Dùng Mẫu 2 | `USER` | Hoạt động |
| `user3@example.com` | Người Dùng Mẫu 3 | `USER` | Hoạt động |
