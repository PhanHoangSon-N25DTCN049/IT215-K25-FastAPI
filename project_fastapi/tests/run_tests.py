import sys
import os
import json
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db
from app.models import UserModel, RoleUser, ProjectModel, ProjectMembersModel, RoleProject
from app.core import hash_password, generate_access_token, generate_refresh_token, settings
from app.services import save_project, join_project, save_refresh_token

# Setup In-memory DB
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_all_api_tests():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)

    results = []

    def record_test(suite, name, method, path, expected_status, actual_status, status, details, payload=None, response_body=None):
        results.append({
            "suite": suite,
            "name": name,
            "method": method,
            "path": path,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "status": status,  # "PASS" or "FAIL"
            "details": details,
            "payload": payload,
            "response": response_body
        })

    # --- 1. Health Check Suite ---
    try:
        res = client.get("/")
        if res.status_code == 200 and res.json().get("message") == "Kết nối database Thành công":
            record_test("Health Check", "GET / - Kiểm tra kết nối DB", "GET", "/", 200, res.status_code, "PASS", "Kết nối thành công", response_body=res.json())
        else:
            record_test("Health Check", "GET / - Kiểm tra kết nối DB", "GET", "/", 200, res.status_code, "FAIL", "Nội dung response không đúng", response_body=res.text)
    except Exception as e:
        record_test("Health Check", "GET / - Kiểm tra kết nối DB", "GET", "/", 200, 500, "FAIL", str(e))

    # --- 2. Auth Suite ---
    # Register Valid
    p_reg = {"email": "tester1@test.com", "password": "Password123!", "full_name": "Tester One"}
    res = client.post("/auth/register", json=p_reg)
    if res.status_code == 201 and res.json().get("statusCode") == 201:
        record_test("Auth", "POST /auth/register - Đăng ký thành công", "POST", "/auth/register", 201, res.status_code, "PASS", "Tạo user mới hợp lệ", p_reg, res.json())
    else:
        record_test("Auth", "POST /auth/register - Đăng ký thành công", "POST", "/auth/register", 201, res.status_code, "FAIL", "Không trả về 201", p_reg, res.text)

    # Register Duplicate Email
    res = client.post("/auth/register", json=p_reg)
    if res.status_code == 409 and res.json().get("statusCode") == 409:
        record_test("Auth", "POST /auth/register - Email trùng lặp", "POST", "/auth/register", 409, res.status_code, "PASS", "Bắt lỗi trùng email chính xác (409)", p_reg, res.json())
    else:
        record_test("Auth", "POST /auth/register - Email trùng lặp", "POST", "/auth/register", 409, res.status_code, "FAIL", "Không bắt được 409", p_reg, res.text)

    # Register Short Password
    p_short = {"email": "short@test.com", "password": "123", "full_name": "Short Pass"}
    res = client.post("/auth/register", json=p_short)
    if res.status_code == 422:
        record_test("Auth", "POST /auth/register - Mật khẩu < 6 ký tự", "POST", "/auth/register", 422, res.status_code, "PASS", "Validation bắt lỗi min_length=6", p_short, res.json())
    else:
        record_test("Auth", "POST /auth/register - Mật khẩu < 6 ký tự", "POST", "/auth/register", 422, res.status_code, "FAIL", "Không bắt lỗi mật khẩu ngắn", p_short, res.text)

    # Register Invalid Email Format
    p_bad_email = {"email": "invalid_email_format", "password": "Password123!", "full_name": "Bad Email"}
    res = client.post("/auth/register", json=p_bad_email)
    if res.status_code == 422:
        record_test("Auth", "POST /auth/register - Email không hợp lệ", "POST", "/auth/register", 422, res.status_code, "PASS", "Validation EmailStr chuẩn", p_bad_email, res.json())
    else:
        record_test("Auth", "POST /auth/register - Email không hợp lệ", "POST", "/auth/register", 422, res.status_code, "FAIL", "Không validate email", p_bad_email, res.text)

    # Login Valid
    res = client.post("/auth/login", data={"email": "tester1@test.com", "password": "Password123!"})
    if res.status_code == 200 and "access_token" in res.json().get("data", {}):
        token_data = res.json()["data"]
        access_token_1 = token_data["access_token"]
        refresh_token_1 = token_data["refresh_token"]
        record_test("Auth", "POST /auth/login - Đăng nhập đúng thông tin", "POST", "/auth/login", 200, res.status_code, "PASS", "Đăng nhập thành công, trả về access + refresh token", response_body=res.json())
    else:
        access_token_1 = None
        refresh_token_1 = None
        record_test("Auth", "POST /auth/login - Đăng nhập đúng thông tin", "POST", "/auth/login", 200, res.status_code, "FAIL", "Đăng nhập thất bại", response_body=res.text)

    # Login Wrong Password
    res = client.post("/auth/login", data={"email": "tester1@test.com", "password": "WrongPassword"})
    if res.status_code == 401:
        record_test("Auth", "POST /auth/login - Sai mật khẩu", "POST", "/auth/login", 401, res.status_code, "PASS", "Báo 401 Thông tin đăng nhập không đúng", response_body=res.json())
    else:
        record_test("Auth", "POST /auth/login - Sai mật khẩu", "POST", "/auth/login", 401, res.status_code, "FAIL", "Không chặn mật khẩu sai", response_body=res.text)

    # Login Non-existent User
    res = client.post("/auth/login", data={"email": "nonexist@test.com", "password": "Password123!"})
    if res.status_code == 401:
        record_test("Auth", "POST /auth/login - Email không tồn tại", "POST", "/auth/login", 401, res.status_code, "PASS", "Báo 401 Không tìm thấy user", response_body=res.json())
    else:
        record_test("Auth", "POST /auth/login - Email không tồn tại", "POST", "/auth/login", 401, res.status_code, "FAIL", "Không trả về 401", response_body=res.text)

    # Login Inactive User
    inactive_user = UserModel(
        email="locked@test.com",
        password_hash=hash_password("Password123!"),
        full_name="Locked User",
        role=RoleUser.USER,
        is_active=False
    )
    db.add(inactive_user)
    db.commit()
    res = client.post("/auth/login", data={"email": "locked@test.com", "password": "Password123!"})
    if res.status_code == 400 and "khóa" in res.text:
        record_test("Auth", "POST /auth/login - Tài khoản bị khóa (is_active=False)", "POST", "/auth/login", 400, res.status_code, "PASS", "Chặn user bị khóa (400)", response_body=res.json())
    else:
        record_test("Auth", "POST /auth/login - Tài khoản bị khóa (is_active=False)", "POST", "/auth/login", 400, res.status_code, "FAIL", "Không chặn user bị khóa", response_body=res.text)

    # Refresh Token Valid
    if refresh_token_1:
        res = client.post("/auth/refresh", json={"refresh_token": refresh_token_1})
        if res.status_code == 201 and "access_token" in res.json().get("data", {}):
            record_test("Auth", "POST /auth/refresh - Refresh token hợp lệ", "POST", "/auth/refresh", 201, res.status_code, "PASS", "Cấp access token mới thành công", response_body=res.json())
        else:
            record_test("Auth", "POST /auth/refresh - Refresh token hợp lệ", "POST", "/auth/refresh", 201, res.status_code, "FAIL", "Refresh token thất bại", response_body=res.text)

    # Refresh Token Revoked
    u1 = db.query(UserModel).filter(UserModel.email == "tester1@test.com").first()
    if u1 and refresh_token_1:
        u1.is_revoked = True
        db.commit()
        res = client.post("/auth/refresh", json={"refresh_token": refresh_token_1})
        if res.status_code == 401 and "không còn hợp lệ" in res.text:
            record_test("Auth", "POST /auth/refresh - Token đã bị revoked", "POST", "/auth/refresh", 401, res.status_code, "PASS", "Chặn token đã thu hồi (401)", response_body=res.json())
        else:
            record_test("Auth", "POST /auth/refresh - Token đã bị revoked", "POST", "/auth/refresh", 401, res.status_code, "FAIL", "Không chặn token bị thu hồi", response_body=res.text)
        u1.is_revoked = False
        db.commit()

    # --- 3. Users Suite ---
    # GET /users/me
    headers_u1 = {"Authorization": f"Bearer {access_token_1}"}
    res = client.get("/users/me", headers=headers_u1)
    if res.status_code == 200 and res.json().get("data", {}).get("email") == "tester1@test.com":
        record_test("Users", "GET /users/me - Lấy thông tin cá nhân", "GET", "/users/me", 200, res.status_code, "PASS", "Trả về đúng thông tin user hiện tại", response_body=res.json())
    else:
        record_test("Users", "GET /users/me - Lấy thông tin cá nhân", "GET", "/users/me", 200, res.status_code, "FAIL", "Không lấy được info", response_body=res.text)

    # GET /users/me without token
    res = client.get("/users/me")
    if res.status_code in [401, 403]:
        record_test("Users", "GET /users/me - Không truyền token", "GET", "/users/me", 401, res.status_code, "PASS", "Chặn truy cập không xác thực", response_body=res.json() if res.status_code != 500 else res.text)
    else:
        record_test("Users", "GET /users/me - Không truyền token", "GET", "/users/me", 401, res.status_code, "FAIL", "Cho phép truy cập không token", response_body=res.text)

    # Regular User Access Admin Endpoint GET /users -> Should be 403
    res = client.get("/users", headers=headers_u1)
    if res.status_code == 403:
        record_test("Users", "GET /users - User thường truy cập danh sách Admin", "GET", "/users", 403, res.status_code, "PASS", "Chặn user thường đúng quyền (403 Forbidden)", response_body=res.json())
    else:
        record_test("Users", "GET /users - User thường truy cập danh sách Admin", "GET", "/users", 403, res.status_code, "FAIL", "Quyền hạn bị vi phạm", response_body=res.text)

    # Admin User Access GET /users -> Should be 200
    admin_user = UserModel(
        email="admin@test.com",
        password_hash=hash_password("AdminPass123!"),
        full_name="Admin Master",
        role=RoleUser.ADMIN,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    admin_token = generate_access_token(admin_user)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    res = client.get("/users", headers=headers_admin)
    if res.status_code == 200:
        record_test("Users", "GET /users - Admin truy cập danh sách user", "GET", "/users", 200, res.status_code, "PASS", "Admin lấy danh sách user thành công", response_body=res.json())
    else:
        record_test("Users", "GET /users - Admin truy cập danh sách user", "GET", "/users", 200, res.status_code, "FAIL", f"BUG: Admin bị chặn 403 do enum str(user.role)='RoleUser.ADMIN' không khớp role checker 'admin'", response_body=res.json())

    # --- 4. Projects Suite ---
    # Create Project Valid
    p_proj = {"name": "Dự án N25DTCN049", "description": "Dự án môn IT215"}
    res = client.post("/project", json=p_proj, headers=headers_u1)
    if res.status_code == 201 and res.json().get("statusCode") == 201:
        proj_data = res.json().get("data", {})
        proj_id = proj_data.get("id")
        record_test("Projects", "POST /project - Tạo dự án mới", "POST", "/project", 201, res.status_code, "PASS", "Tạo project thành công, gán role owner", p_proj, res.json())
    else:
        proj_id = None
        record_test("Projects", "POST /project - Tạo dự án mới", "POST", "/project", 201, res.status_code, "FAIL", "Không tạo được project", p_proj, res.text)

    # List Projects
    res = client.get("/project", headers=headers_u1)
    if res.status_code == 200 and len(res.json().get("data", [])) >= 1:
        record_test("Projects", "GET /project - Lấy danh sách dự án của user", "GET", "/project", 200, res.status_code, "PASS", "Lấy đúng danh sách dự án user tham gia", response_body=res.json())
    else:
        record_test("Projects", "GET /project - Lấy danh sách dự án của user", "GET", "/project", 200, res.status_code, "FAIL", "Lấy danh sách thất bại", response_body=res.text)

    # Search Projects
    res = client.get("/project?search=N25DTCN049", headers=headers_u1)
    if res.status_code == 200 and len(res.json().get("data", [])) == 1:
        record_test("Projects", "GET /project?search=... - Tìm kiếm dự án theo tên", "GET", "/project", 200, res.status_code, "PASS", "Tìm kiếm chính xác", response_body=res.json())
    else:
        record_test("Projects", "GET /project?search=... - Tìm kiếm dự án theo tên", "GET", "/project", 200, res.status_code, "FAIL", "Tìm kiếm không đúng", response_body=res.text)

    # Get Project Detail as Owner
    if proj_id:
        res = client.get(f"/project/{proj_id}", headers=headers_u1)
        if res.status_code == 200 and res.json().get("data", {}).get("role_user") == "owner":
            record_test("Projects", "GET /project/{id} - Xem chi tiết dự án (Owner)", "GET", f"/project/{proj_id}", 200, res.status_code, "PASS", "Lấy chi tiết dự án thành công, role owner", response_body=res.json())
        else:
            record_test("Projects", "GET /project/{id} - Xem chi tiết dự án (Owner)", "GET", f"/project/{proj_id}", 200, res.status_code, "FAIL", "Chi tiết không đúng", response_body=res.text)

    # Create User 2
    u2 = UserModel(
        email="tester2@test.com",
        password_hash=hash_password("Password123!"),
        full_name="Tester Two",
        role=RoleUser.USER,
        is_active=True
    )
    db.add(u2)
    db.commit()
    db.refresh(u2)
    token_u2 = generate_access_token(u2)
    headers_u2 = {"Authorization": f"Bearer {token_u2}"}

    # Get Project Detail as Non-member -> Should be 403
    if proj_id:
        res = client.get(f"/project/{proj_id}", headers=headers_u2)
        if res.status_code == 403:
            record_test("Projects", "GET /project/{id} - Người ngoài xem dự án riêng tư", "GET", f"/project/{proj_id}", 403, res.status_code, "PASS", "Bảo mật tốt: Chặn non-member truy cập (403)", response_body=res.json())
        else:
            record_test("Projects", "GET /project/{id} - Người ngoài xem dự án riêng tư", "GET", f"/project/{proj_id}", 403, res.status_code, "FAIL", "Hở quyền dữ liệu dự án", response_body=res.text)

    # Add Member to Project (Owner adds User 2)
    if proj_id:
        p_mem = {"user_id": u2.id, "role": "member"}
        res = client.post(f"/project/{proj_id}/member", json=p_mem, headers=headers_u1)
        if res.status_code == 201:
            record_test("Projects", "POST /project/{id}/member - Owner thêm thành viên mới", "POST", f"/project/{proj_id}/member", 201, res.status_code, "PASS", "Thêm member thành công với status 201 Created", p_mem, res.json())
        else:
            record_test("Projects", "POST /project/{id}/member - Owner thêm thành viên mới", "POST", f"/project/{proj_id}/member", 201, res.status_code, "FAIL", "Không thêm được member", p_mem, res.text)

    # Non-owner Member adds Member -> Should be 403
    if proj_id:
        p_mem3 = {"user_id": admin_user.id, "role": "member"}
        res = client.post(f"/project/{proj_id}/member", json=p_mem3, headers=headers_u2)
        if res.status_code == 403:
            record_test("Projects", "POST /project/{id}/member - Member thường thêm người khác", "POST", f"/project/{proj_id}/member", 403, res.status_code, "PASS", "Chặn member thường cấp quyền (403)", p_mem3, res.json())
        else:
            record_test("Projects", "POST /project/{id}/member - Member thường thêm người khác", "POST", f"/project/{proj_id}/member", 403, res.status_code, "FAIL", "Member thường lại thêm được người", p_mem3, res.text)

    # Update Project (Owner)
    if proj_id:
        p_up = {"name": "Dự án N25DTCN049 - Cập nhật", "description": "Mô tả mới"}
        res = client.patch(f"/project/{proj_id}", json=p_up, headers=headers_u1)
        if res.status_code == 200 and res.json().get("data", {}).get("name") == "Dự án N25DTCN049 - Cập nhật":
            record_test("Projects", "PATCH /project/{id} - Owner cập nhật dự án", "PATCH", f"/project/{proj_id}", 200, res.status_code, "PASS", "Cập nhật thành công", p_up, res.json())
        else:
            record_test("Projects", "PATCH /project/{id} - Owner cập nhật dự án", "PATCH", f"/project/{proj_id}", 200, res.status_code, "FAIL", "Cập nhật thất bại", p_up, res.text)

    # Update Project (Non-owner member) -> Should be 403
    if proj_id:
        p_hack = {"name": "Tên bị hack"}
        res = client.patch(f"/project/{proj_id}", json=p_hack, headers=headers_u2)
        if res.status_code == 403:
            record_test("Projects", "PATCH /project/{id} - Member thường sửa dự án", "PATCH", f"/project/{proj_id}", 403, res.status_code, "PASS", "Chặn sửa dự án khi không phải Owner (403)", p_hack, res.json())
        else:
            record_test("Projects", "PATCH /project/{id} - Member thường sửa dự án", "PATCH", f"/project/{proj_id}", 403, res.status_code, "FAIL", "Member thường sửa được dự án", p_hack, res.text)

    # Delete Member with Non-existent ID -> Should return 404
    if proj_id:
        res = client.delete(f"/project/{proj_id}/members/999999", headers=headers_u1)
        if res.status_code == 404 and "Không tồn tại Member cần xóa" in res.text:
            record_test("Projects", "DELETE /project/{id}/members/{user_id} - Xóa member không tồn tại", "DELETE", f"/project/{proj_id}/members/999999", 404, res.status_code, "PASS", "Báo 404 Không tồn tại Member cần xóa", response_body=res.json())
        else:
            record_test("Projects", "DELETE /project/{id}/members/{user_id} - Xóa member không tồn tại", "DELETE", f"/project/{proj_id}/members/999999", 404, res.status_code, "FAIL", "Không trả về 404", response_body=res.text)

    # Delete Member Logic (user_id) -> Should return 204 No Content
    if proj_id:
        res = client.delete(f"/project/{proj_id}/members/{u2.id}", headers=headers_u1)
        if res.status_code == 204:
            record_test("Projects", "DELETE /project/{id}/members/{user_id} - Xóa thành viên theo user_id", "DELETE", f"/project/{proj_id}/members/{u2.id}", 204, res.status_code, "PASS", "Xóa thành viên khỏi project thành công (204 No Content)")
        else:
            record_test("Projects", "DELETE /project/{id}/members/{user_id} - Xóa thành viên theo user_id", "DELETE", f"/project/{proj_id}/members/{u2.id}", 204, res.status_code, "FAIL", "Xóa thành viên thất bại", response_body=res.text)

    # Delete Project (Non-owner) -> Should be 403
    if proj_id:
        res = client.delete(f"/project/{proj_id}", headers=headers_u2)
        if res.status_code == 403:
            record_test("Projects", "DELETE /project/{id} - Member thường xóa dự án", "DELETE", f"/project/{proj_id}", 403, res.status_code, "PASS", "Chặn xóa dự án khi không phải Owner (403)", response_body=res.json())
        else:
            record_test("Projects", "DELETE /project/{id} - Member thường xóa dự án", "DELETE", f"/project/{proj_id}", 403, res.status_code, "FAIL", "Member xóa được dự án", response_body=res.text)

    # --- 5. Tasks Suite ---
    task_id = None
    if proj_id:
        # Create Task (Owner)
        p_task = {
            "title": "Build FastAPI Module",
            "description": "Implement authentication and project routers",
            "due_date": "2026-12-31T23:59:59",
            "priority": "high"
        }
        res = client.post(f"/project/{proj_id}/tasks", json=p_task, headers=headers_u1)
        if res.status_code == 201 and res.json().get("statusCode") == 201:
            task_id = res.json().get("data", {}).get("id")
            record_test("Tasks", "POST /project/{id}/tasks - Tạo task mới", "POST", f"/project/{proj_id}/tasks", 201, res.status_code, "PASS", "Tạo task thành công", p_task, res.json())
        else:
            record_test("Tasks", "POST /project/{id}/tasks - Tạo task mới", "POST", f"/project/{proj_id}/tasks", 201, res.status_code, "FAIL", "Không tạo được task", p_task, res.text)

        # Get Tasks List with filters
        res = client.get(f"/project/{proj_id}/tasks?priority=high&page=1&size=10", headers=headers_u1)
        if res.status_code == 200:
            record_test("Tasks", "GET /project/{id}/tasks - Lấy danh sách task kèm filter", "GET", f"/project/{proj_id}/tasks", 200, res.status_code, "PASS", "Lấy danh sách task thành công", response_body=res.json())
        else:
            record_test("Tasks", "GET /project/{id}/tasks - Lấy danh sách task kèm filter", "GET", f"/project/{proj_id}/tasks", 200, res.status_code, "FAIL", "Lấy danh sách task thất bại", response_body=res.text)

        # Get Task Detail
        if task_id:
            res = client.get(f"/tasks/{task_id}", headers=headers_u1)
            if res.status_code == 200:
                record_test("Tasks", "GET /tasks/{id} - Xem chi tiết task", "GET", f"/tasks/{task_id}", 200, res.status_code, "PASS", "Lấy chi tiết task thành công", response_body=res.json())
            else:
                record_test("Tasks", "GET /tasks/{id} - Xem chi tiết task", "GET", f"/tasks/{task_id}", 200, res.status_code, "FAIL", "Lấy chi tiết task thất bại", response_body=res.text)

        # Update Task (Owner)
        if task_id:
            p_update_task = {"status": "in_progress", "title": "Updated Task Title"}
            res = client.patch(f"/tasks/{task_id}", json=p_update_task, headers=headers_u1)
            if res.status_code == 200:
                record_test("Tasks", "PATCH /tasks/{id} - Cập nhật task", "PATCH", f"/tasks/{task_id}", 200, res.status_code, "PASS", "Cập nhật task thành công", p_update_task, res.json())
            else:
                record_test("Tasks", "PATCH /tasks/{id} - Cập nhật task", "PATCH", f"/tasks/{task_id}", 200, res.status_code, "FAIL", "Cập nhật task thất bại", p_update_task, res.text)

        # Delete Task (Owner)
        if task_id:
            res = client.delete(f"/tasks/{task_id}", headers=headers_u1)
            if res.status_code == 204:
                record_test("Tasks", "DELETE /tasks/{id} - Xóa task", "DELETE", f"/tasks/{task_id}", 204, res.status_code, "PASS", "Xóa task thành công (204 No Content)")
            else:
                record_test("Tasks", "DELETE /tasks/{id} - Xóa task", "DELETE", f"/tasks/{task_id}", 204, res.status_code, "FAIL", "Xóa task thất bại", response_body=res.text)

    # Delete Project (Owner)
    if proj_id:
        res = client.delete(f"/project/{proj_id}", headers=headers_u1)
        if res.status_code == 204:
            record_test("Projects", "DELETE /project/{id} - Owner xóa dự án", "DELETE", f"/project/{proj_id}", 204, res.status_code, "PASS", "Xóa dự án thành công (204 No Content)")
        else:
            record_test("Projects", "DELETE /project/{id} - Owner xóa dự án", "DELETE", f"/project/{proj_id}", 204, res.status_code, "FAIL", "Xóa dự án thất bại", response_body=res.text)

    # Summary Statistics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["status"] == "PASS")
    failed_tests = sum(1 for r in results if r["status"] == "FAIL")

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "pass_rate": f"{(passed_tests / total_tests) * 100:.1f}%",
        "results": results
    }

    with open("test_execution_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n================ TEST EXECUTION SUMMARY ================")
    print(f"Total Tests : {total_tests}")
    print(f"Passed      : {passed_tests} ({summary['pass_rate']})")
    print(f"Failed      : {failed_tests}")
    print(f"========================================================\n")

    for r in results:
        sym = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"[{sym}] [{r['suite']}] {r['method']} {r['path']} -> Expected {r['expected_status']}, Got {r['actual_status']} | {r['name']}")

if __name__ == "__main__":
    run_all_api_tests()
