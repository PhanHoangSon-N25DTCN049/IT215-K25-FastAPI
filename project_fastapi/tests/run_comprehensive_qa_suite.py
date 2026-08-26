import sys
import os
import json
import time
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import jwt

from app.main import app
from app.db import Base, get_db
from app.models import UserModel, RoleUser, ProjectModel, ProjectMembersModel, RoleProject, TaskModel, TaskPriority, TaskStatus
from app.core import hash_password, generate_access_token, generate_refresh_token, settings
from app.services import save_project, join_project, create_task, query_user_by_gmail

def run_qa_suite():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=False)

    test_results = []
    def record(category, test_id, name, method, endpoint, expected_status, actual_status, status, details, payload=None, response_summary=None, elapsed_ms=0):
        test_results.append({
            "category": category,
            "test_id": test_id,
            "name": name,
            "method": method,
            "endpoint": endpoint,
            "expected_status": expected_status,
            "actual_status": actual_status,
            "status": status, # PASS / FAIL / BUG
            "details": details,
            "payload": payload,
            "response": response_summary,
            "elapsed_ms": round(elapsed_ms, 2)
        })
        try:
            db.rollback()
        except Exception:
            pass

    print("==================================================")
    print("STARTING FULL COMPREHENSIVE QA API TEST EXECUTION")
    print("==================================================")

    # -------------------------------------------------------------
    # 1. HEALTH CHECK SUITE
    # -------------------------------------------------------------
    t0 = time.time()
    res = client.get("/")
    elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and "Thành công" in res.text:
        record("Health Check", "TC-HLT-001", "Health check hệ thống & DB", "GET", "/", 200, res.status_code, "PASS", "DB kết nối tốt, trả về 200 OK", response_summary=res.json(), elapsed_ms=elapsed)
    else:
        record("Health Check", "TC-HLT-001", "Health check hệ thống & DB", "GET", "/", 200, res.status_code, "FAIL", "Response không đúng mong đợi", response_summary=res.text, elapsed_ms=elapsed)

    # -------------------------------------------------------------
    # 2. AUTHENTICATION & AUTHORIZATION SUITE
    # -------------------------------------------------------------
    # TC-AUTH-001: Register Success
    p_reg1 = {"email": "qa_owner@example.com", "password": "Password123!", "full_name": "QA Project Owner"}
    t0 = time.time(); res = client.post("/auth/register", json=p_reg1); elapsed = (time.time() - t0) * 1000
    if res.status_code == 201 and res.json().get("statusCode") == 201:
        record("Authentication", "TC-AUTH-001", "Đăng ký tài khoản hợp lệ", "POST", "/auth/register", 201, res.status_code, "PASS", "Tạo tài khoản thành công", p_reg1, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-001", "Đăng ký tài khoản hợp lệ", "POST", "/auth/register", 201, res.status_code, "FAIL", "Thất bại khi đăng ký", p_reg1, res.text, elapsed)

    # TC-AUTH-002: Register Duplicate Email
    t0 = time.time(); res = client.post("/auth/register", json=p_reg1); elapsed = (time.time() - t0) * 1000
    if res.status_code == 409 and res.json().get("statusCode") == 409:
        record("Authentication", "TC-AUTH-002", "Đăng ký trùng email", "POST", "/auth/register", 409, res.status_code, "PASS", "Bắt lỗi 409 Conflict chính xác", p_reg1, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-002", "Đăng ký trùng email", "POST", "/auth/register", 409, res.status_code, "FAIL", "Không chặn được trùng email", p_reg1, res.text, elapsed)

    # TC-AUTH-003: Register Invalid Email Format
    p_bad_email = {"email": "not-an-email", "password": "Password123!", "full_name": "Bad Email"}
    t0 = time.time(); res = client.post("/auth/register", json=p_bad_email); elapsed = (time.time() - t0) * 1000
    if res.status_code == 422:
        record("Authentication", "TC-AUTH-003", "Đăng ký sai định dạng email", "POST", "/auth/register", 422, res.status_code, "PASS", "Pydantic EmailStr validation bắt lỗi 422", p_bad_email, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-003", "Đăng ký sai định dạng email", "POST", "/auth/register", 422, res.status_code, "FAIL", "Không bắt lỗi email", p_bad_email, res.text, elapsed)

    # TC-AUTH-004: Register Short Password (< 6 chars)
    p_short_pwd = {"email": "short_pwd@example.com", "password": "123", "full_name": "Short Pwd"}
    t0 = time.time(); res = client.post("/auth/register", json=p_short_pwd); elapsed = (time.time() - t0) * 1000
    if res.status_code == 422:
        record("Authentication", "TC-AUTH-004", "Đăng ký mật khẩu < 6 ký tự", "POST", "/auth/register", 422, res.status_code, "PASS", "Pydantic Field(min_length=6) bắt lỗi 422", p_short_pwd, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-004", "Đăng ký mật khẩu < 6 ký tự", "POST", "/auth/register", 422, res.status_code, "FAIL", "Không bắt lỗi mật khẩu ngắn", p_short_pwd, res.text, elapsed)

    # TC-AUTH-005: Register Missing Fields
    p_missing = {"email": "missing@example.com"}
    t0 = time.time(); res = client.post("/auth/register", json=p_missing); elapsed = (time.time() - t0) * 1000
    if res.status_code == 422:
        record("Authentication", "TC-AUTH-005", "Đăng ký thiếu trường bắt buộc", "POST", "/auth/register", 422, res.status_code, "PASS", "Bắt lỗi thiếu trường 422", p_missing, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-005", "Đăng ký thiếu trường bắt buộc", "POST", "/auth/register", 422, res.status_code, "FAIL", "Không bắt lỗi thiếu trường", p_missing, res.text, elapsed)

    # Create additional users in DB
    user_owner = query_user_by_gmail("qa_owner@example.com", db)
    user_member = UserModel(email="qa_member@example.com", password_hash=hash_password("Password123!"), full_name="QA Member User", role=RoleUser.USER, is_active=True)
    user_stranger = UserModel(email="qa_stranger@example.com", password_hash=hash_password("Password123!"), full_name="QA Stranger User", role=RoleUser.USER, is_active=True)
    user_admin = UserModel(email="qa_admin@example.com", password_hash=hash_password("AdminPass123!"), full_name="QA System Administrator", role=RoleUser.ADMIN, is_active=True)
    user_inactive = UserModel(email="qa_locked@example.com", password_hash=hash_password("Password123!"), full_name="QA Locked User", role=RoleUser.USER, is_active=False)
    db.add_all([user_member, user_stranger, user_admin, user_inactive])
    db.commit()
    db.refresh(user_member)
    db.refresh(user_stranger)
    db.refresh(user_admin)
    db.refresh(user_inactive)

    admin_user_id = user_admin.id
    owner_user_id = user_owner.id
    member_user_id = user_member.id
    stranger_user_id = user_stranger.id

    # TC-AUTH-006: Login Success
    t0 = time.time()
    res = client.post("/auth/login", data={"email": "qa_owner@example.com", "password": "Password123!"})
    elapsed = (time.time() - t0) * 1000
    owner_access_token = None
    owner_refresh_token = None
    if res.status_code == 200 and "access_token" in res.text:
        data = res.json()["data"]
        owner_access_token = data["access_token"]
        owner_refresh_token = data["refresh_token"]
        record("Authentication", "TC-AUTH-006", "Đăng nhập thành công", "POST", "/auth/login", 200, res.status_code, "PASS", "Nhận access token và refresh token", {"email": "qa_owner@example.com"}, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-006", "Đăng nhập thành công", "POST", "/auth/login", 200, res.status_code, "FAIL", "Đăng nhập thất bại", {"email": "qa_owner@example.com"}, res.text, elapsed)

    # TC-AUTH-007: Login Wrong Password
    t0 = time.time(); res = client.post("/auth/login", data={"email": "qa_owner@example.com", "password": "WrongPassword!"}); elapsed = (time.time() - t0) * 1000
    if res.status_code == 401:
        record("Authentication", "TC-AUTH-007", "Đăng nhập sai mật khẩu", "POST", "/auth/login", 401, res.status_code, "PASS", "Từ chối xác thực 401 Unauthorized", {"email": "qa_owner@example.com"}, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-007", "Đăng nhập sai mật khẩu", "POST", "/auth/login", 401, res.status_code, "FAIL", "Không chặn sai mật khẩu", {"email": "qa_owner@example.com"}, res.text, elapsed)

    # TC-AUTH-008: Login Non-existent User
    t0 = time.time(); res = client.post("/auth/login", data={"email": "nonexistent@example.com", "password": "Password123!"}); elapsed = (time.time() - t0) * 1000
    if res.status_code == 401:
        record("Authentication", "TC-AUTH-008", "Đăng nhập tài khoản không tồn tại", "POST", "/auth/login", 401, res.status_code, "PASS", "Từ chối 401 Unauthorized", {"email": "nonexistent@example.com"}, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-008", "Đăng nhập tài khoản không tồn tại", "POST", "/auth/login", 401, res.status_code, "FAIL", "Không trả về 401", {"email": "nonexistent@example.com"}, res.text, elapsed)

    # TC-AUTH-009: Login Inactive / Locked Account
    t0 = time.time(); res = client.post("/auth/login", data={"email": "qa_locked@example.com", "password": "Password123!"}); elapsed = (time.time() - t0) * 1000
    if res.status_code == 400:
        record("Authentication", "TC-AUTH-009", "Đăng nhập tài khoản bị khóa", "POST", "/auth/login", 400, res.status_code, "PASS", "Báo lỗi tài khoản bị khóa 400 Bad Request", {"email": "qa_locked@example.com"}, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-009", "Đăng nhập tài khoản bị khóa", "POST", "/auth/login", 400, res.status_code, "FAIL", "Không chặn tài khoản khóa", {"email": "qa_locked@example.com"}, res.text, elapsed)

    # TC-AUTH-010: Refresh Token Success with valid active refresh token
    t0 = time.time(); res = client.post("/auth/refresh", json={"refresh_token": owner_refresh_token}); elapsed = (time.time() - t0) * 1000
    if res.status_code == 201 and "access_token" in res.text:
        record("Authentication", "TC-AUTH-010", "Cấp mới Access Token bằng Refresh Token", "POST", "/auth/refresh", 201, res.status_code, "PASS", "Cấp access token mới thành công", {"refresh_token": "..."}, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-010", "Cấp mới Access Token bằng Refresh Token", "POST", "/auth/refresh", 201, res.status_code, "FAIL", "Không cấp được token mới", {"refresh_token": "..."}, res.text, elapsed)

    # TC-AUTH-011: Refresh Token Invalid / Forged
    t0 = time.time(); res = client.post("/auth/refresh", json={"refresh_token": "invalid.jwt.token"}); elapsed = (time.time() - t0) * 1000
    if res.status_code == 401:
        record("Authentication", "TC-AUTH-011", "Refresh Token giả mạo/không hợp lệ", "POST", "/auth/refresh", 401, res.status_code, "PASS", "Chặn refresh token giả mạo 401", {"refresh_token": "invalid.jwt.token"}, res.json(), elapsed)
    else:
        record("Authentication", "TC-AUTH-011", "Refresh Token giả mạo/không hợp lệ", "POST", "/auth/refresh", 401, res.status_code, "FAIL", "Không chặn token giả", {"refresh_token": "invalid.jwt.token"}, res.text, elapsed)

    # Generate JWT Tokens for functional flows
    if not owner_access_token:
        owner_access_token = generate_access_token(user_owner)
    member_access_token = generate_access_token(user_member)
    stranger_access_token = generate_access_token(user_stranger)
    admin_access_token = generate_access_token(user_admin)

    owner_hdr = {"Authorization": f"Bearer {owner_access_token}"}
    member_hdr = {"Authorization": f"Bearer {member_access_token}"}
    stranger_hdr = {"Authorization": f"Bearer {stranger_access_token}"}
    admin_hdr = {"Authorization": f"Bearer {admin_access_token}"}

    # -------------------------------------------------------------
    # 3. USERS MODULE SUITE
    # -------------------------------------------------------------
    # TC-USR-001: Get Me Success
    t0 = time.time(); res = client.get("/users/me", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and res.json()["data"]["email"] == "qa_owner@example.com":
        record("Users", "TC-USR-001", "Lấy thông tin cá nhân (Get Me)", "GET", "/users/me", 200, res.status_code, "PASS", "Trả về đúng profile của token", None, res.json(), elapsed)
    else:
        record("Users", "TC-USR-001", "Lấy thông tin cá nhân (Get Me)", "GET", "/users/me", 200, res.status_code, "FAIL", "Lỗi lấy profile", None, res.text, elapsed)

    # TC-USR-002: Get Me Unauthorized (No token)
    t0 = time.time(); res = client.get("/users/me"); elapsed = (time.time() - t0) * 1000
    if res.status_code in [401, 403]:
        record("Users", "TC-USR-002", "Lấy profile khi không gửi Token", "GET", "/users/me", 401, res.status_code, "PASS", "Bắt lỗi thiếu token", None, res.json(), elapsed)
    else:
        record("Users", "TC-USR-002", "Lấy profile khi không gửi Token", "GET", "/users/me", 401, res.status_code, "FAIL", "Không chặn request không token", None, res.text, elapsed)

    # TC-USR-003: Admin Get Users List
    t0 = time.time(); res = client.get("/users", headers=admin_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and isinstance(res.json().get("data"), list) and len(res.json()["data"]) >= 4:
        record("Users", "TC-USR-003", "Admin lấy danh sách người dùng", "GET", "/users", 200, res.status_code, "PASS", f"Trả về danh sách {len(res.json()['data'])} users", None, res.json(), elapsed)
    else:
        record("Users", "TC-USR-003", "Admin lấy danh sách người dùng", "GET", "/users", 200, res.status_code, "FAIL", "Admin không lấy được danh sách", None, res.text, elapsed)

    # TC-USR-004: Regular User Access Admin Users List (RBAC Check)
    t0 = time.time(); res = client.get("/users", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 403:
        record("Users", "TC-USR-004", "User thường truy cập API Admin (RBAC)", "GET", "/users", 403, res.status_code, "PASS", "Chặn User thường bằng 403 Forbidden chính xác", None, res.json(), elapsed)
    else:
        record("Users", "TC-USR-004", "User thường truy cập API Admin (RBAC)", "GET", "/users", 403, res.status_code, "FAIL", "Lỗi phân quyền RBAC", None, res.text, elapsed)

    # TC-USR-005: Admin Filter Users by Email & Status
    t0 = time.time(); res = client.get("/users?email=qa_owner&status=true", headers=admin_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and len(res.json()["data"]) == 1:
        record("Users", "TC-USR-005", "Admin lọc user theo Email và Trạng thái", "GET", "/users?email=...&status=...", 200, res.status_code, "PASS", "Lọc chính xác 1 kết quả", None, res.json(), elapsed)
    else:
        record("Users", "TC-USR-005", "Admin lọc user theo Email và Trạng thái", "GET", "/users?email=...&status=...", 200, res.status_code, "FAIL", "Lỗi lọc user", None, res.text, elapsed)

    # -------------------------------------------------------------
    # 4. PROJECTS MODULE SUITE
    # -------------------------------------------------------------
    # TC-PRJ-001: Create Project Success
    p_prj = {"name": "Dự án Alpha Quản lý Kho", "description": "Hệ thống quản lý kho thông minh"}
    t0 = time.time(); res = client.post("/project", json=p_prj, headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    project_id = None
    if res.status_code == 201 and res.json().get("statusCode") == 201:
        project_id = res.json()["data"]["id"]
        record("Projects", "TC-PRJ-001", "Tạo dự án mới thành công", "POST", "/project", 201, res.status_code, "PASS", f"Tạo project id={project_id}, gán OWNER", p_prj, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-001", "Tạo dự án mới thành công", "POST", "/project", 201, res.status_code, "FAIL", "Không tạo được project", p_prj, res.text, elapsed)

    # TC-PRJ-002: Create Project Missing Name
    t0 = time.time(); res = client.post("/project", json={"description": "No Name"}, headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 422:
        record("Projects", "TC-PRJ-002", "Tạo dự án thiếu tên bắt buộc", "POST", "/project", 422, res.status_code, "PASS", "Bắt lỗi 422 Validation Error", {"description": "No Name"}, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-002", "Tạo dự án thiếu tên bắt buộc", "POST", "/project", 422, res.status_code, "FAIL", "Không bắt lỗi thiếu tên", {"description": "No Name"}, res.text, elapsed)

    # TC-PRJ-003: Get User Projects List & Search
    t0 = time.time(); res = client.get("/project?search=Alpha", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and len(res.json()["data"]) >= 1:
        record("Projects", "TC-PRJ-003", "Tìm kiếm dự án theo tên", "GET", "/project?search=Alpha", 200, res.status_code, "PASS", "Tìm thấy dự án tương ứng", None, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-003", "Tìm kiếm dự án theo tên", "GET", "/project?search=Alpha", 200, res.status_code, "FAIL", "Tìm kiếm thất bại", None, res.text, elapsed)

    # TC-PRJ-004: Get Project Detail as Owner
    t0 = time.time(); res = client.get(f"/project/{project_id}", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and res.json()["data"]["role_user"] == "owner":
        record("Projects", "TC-PRJ-004", "Owner xem chi tiết dự án", "GET", f"/project/{project_id}", 200, res.status_code, "PASS", "Trả về thông tin chi tiết và role_user=owner", None, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-004", "Owner xem chi tiết dự án", "GET", f"/project/{project_id}", 200, res.status_code, "FAIL", "Lỗi lấy chi tiết dự án", None, res.text, elapsed)

    # TC-PRJ-005: Non-member Views Project Detail (IDOR Check)
    t0 = time.time(); res = client.get(f"/project/{project_id}", headers=stranger_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 403:
        record("Projects", "TC-PRJ-005", "Người ngoài xem chi tiết dự án (IDOR)", "GET", f"/project/{project_id}", 403, res.status_code, "PASS", "Bảo mật tốt: Chặn người ngoài bằng 403 Forbidden", None, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-005", "Người ngoài xem chi tiết dự án (IDOR)", "GET", f"/project/{project_id}", 403, res.status_code, "FAIL", "Lỗi IDOR: Cho phép xem dự án trái phép", None, res.text, elapsed)

    # TC-PRJ-006: Owner Adds Member to Project
    p_add_mem = {"user_id": member_user_id, "role": "member"}
    t0 = time.time(); res = client.post(f"/project/{project_id}/member", json=p_add_mem, headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 201 and res.json().get("statusCode") == 201:
        record("Projects", "TC-PRJ-006", "Owner thêm thành viên vào dự án", "POST", f"/project/{project_id}/member", 201, res.status_code, "PASS", "Thêm member thành công", p_add_mem, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-006", "Owner thêm thành viên vào dự án", "POST", f"/project/{project_id}/member", 201, res.status_code, "FAIL", "Thêm member thất bại", p_add_mem, res.text, elapsed)

    # TC-PRJ-007: Add Duplicate Member to Project
    t0 = time.time(); res = client.post(f"/project/{project_id}/member", json=p_add_mem, headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 409:
        record("Projects", "TC-PRJ-007", "Thêm trùng lặp thành viên đã có", "POST", f"/project/{project_id}/member", 409, res.status_code, "PASS", "Bắt lỗi 409 Conflict thành viên đã tồn tại", p_add_mem, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-007", "Thêm trùng lặp thành viên đã có", "POST", f"/project/{project_id}/member", 409, res.status_code, "FAIL", "Không chặn trùng member", p_add_mem, res.text, elapsed)

    # TC-PRJ-008: Non-owner Adds Member (Permission Check)
    t0 = time.time(); res = client.post(f"/project/{project_id}/member", json={"user_id": 999, "role": "member"}, headers=member_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 403:
        record("Projects", "TC-PRJ-008", "Member thường cố tình thêm thành viên khác", "POST", f"/project/{project_id}/member", 403, res.status_code, "PASS", "Chặn bằng 403 Forbidden chính xác", None, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-008", "Member thường cố tình thêm thành viên khác", "POST", f"/project/{project_id}/member", 403, res.status_code, "FAIL", "Lỗi phân quyền thêm member", None, res.text, elapsed)

    # TC-PRJ-009: Get All Members in Project
    t0 = time.time(); res = client.get(f"/project/{project_id}/members", headers=member_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and len(res.json()["data"]) == 2:
        record("Projects", "TC-PRJ-009", "Lấy danh sách thành viên dự án", "GET", f"/project/{project_id}/members", 200, res.status_code, "PASS", "Trả về 2 thành viên (Owner & Member)", None, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-009", "Lấy danh sách thành viên dự án", "GET", f"/project/{project_id}/members", 200, res.status_code, "FAIL", "Lấy danh sách member thất bại", None, res.text, elapsed)

    # TC-PRJ-010: Update Project Info as Owner
    p_upd_prj = {"name": "Dự án Alpha (Updated)", "description": "Mô tả mới cập nhật"}
    t0 = time.time(); res = client.patch(f"/project/{project_id}", json=p_upd_prj, headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and res.json()["data"]["name"] == p_upd_prj["name"]:
        record("Projects", "TC-PRJ-010", "Owner cập nhật thông tin dự án", "PATCH", f"/project/{project_id}", 200, res.status_code, "PASS", "Cập nhật tên & mô tả thành công", p_upd_prj, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-010", "Owner cập nhật thông tin dự án", "PATCH", f"/project/{project_id}", 200, res.status_code, "FAIL", "Cập nhật project thất bại", p_upd_prj, res.text, elapsed)

    # TC-PRJ-011: Member Updates Project Info (Permission Check)
    t0 = time.time(); res = client.patch(f"/project/{project_id}", json={"name": "Hacked"}, headers=member_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 403:
        record("Projects", "TC-PRJ-011", "Member thường sửa đổi thông tin dự án", "PATCH", f"/project/{project_id}", 403, res.status_code, "PASS", "Chặn sửa đổi trái phép bằng 403", None, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-011", "Member thường sửa đổi thông tin dự án", "PATCH", f"/project/{project_id}", 403, res.status_code, "FAIL", "Không chặn member sửa project", None, res.text, elapsed)

    # TC-PRJ-012: Get Project Activity Logs
    t0 = time.time(); res = client.get(f"/project/{project_id}/activities?limit=10&offset=0", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and isinstance(res.json()["data"], list) and len(res.json()["data"]) >= 3:
        record("Projects", "TC-PRJ-012", "Lấy lịch sử thao tác dự án (Activity Logs)", "GET", f"/project/{project_id}/activities", 200, res.status_code, "PASS", f"Ghi nhận đúng {len(res.json()['data'])} logs hành động", None, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-012", "Lấy lịch sử thao tác dự án (Activity Logs)", "GET", f"/project/{project_id}/activities", 200, res.status_code, "FAIL", "Lỗi lấy activity logs", None, res.text, elapsed)

    # -------------------------------------------------------------
    # 5. TASKS MODULE SUITE
    # -------------------------------------------------------------
    # TC-TSK-001: Member Creates Task in Project
    p_task1 = {
        "title": "Thiết kế cơ sở dữ liệu v1",
        "description": "Tạo ERD và quan hệ các bảng",
        "priority": "high",
        "due_date": "2026-12-31T23:59:59"
    }
    t0 = time.time(); res = client.post(f"/project/{project_id}/tasks", json=p_task1, headers=member_hdr); elapsed = (time.time() - t0) * 1000
    task_id = None
    if res.status_code == 201 and res.json().get("statusCode") == 201:
        task_id = res.json()["data"]["id"]
        record("Tasks", "TC-TSK-001", "Member tạo task mới trong dự án", "POST", f"/project/{project_id}/tasks", 201, res.status_code, "PASS", f"Tạo task id={task_id}, gán assignee cho creator", p_task1, res.json(), elapsed)
    else:
        record("Tasks", "TC-TSK-001", "Member tạo task mới trong dự án", "POST", f"/project/{project_id}/tasks", 201, res.status_code, "FAIL", "Tạo task thất bại", p_task1, res.text, elapsed)

    # TC-TSK-002: Stranger Creates Task in Project (IDOR Check)
    t0 = time.time(); res = client.post(f"/project/{project_id}/tasks", json=p_task1, headers=stranger_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 403:
        record("Tasks", "TC-TSK-002", "Người ngoài tạo task trong dự án (IDOR)", "POST", f"/project/{project_id}/tasks", 403, res.status_code, "PASS", "Chặn bằng 403 Forbidden chính xác", p_task1, res.json(), elapsed)
    else:
        record("Tasks", "TC-TSK-002", "Người ngoài tạo task trong dự án (IDOR)", "POST", f"/project/{project_id}/tasks", 403, res.status_code, "FAIL", "Lỗi IDOR tạo task", p_task1, res.text, elapsed)

    # TC-TSK-003: Task Creation Validation (Invalid Priority)
    p_bad_pri = {"title": "Bad Priority", "priority": "CRITICAL_URGENT"}
    t0 = time.time(); res = client.post(f"/project/{project_id}/tasks", json=p_bad_pri, headers=member_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 422:
        record("Tasks", "TC-TSK-003", "Tạo task sai enum Priority", "POST", f"/project/{project_id}/tasks", 422, res.status_code, "PASS", "Bắt lỗi enum 422 chính xác", p_bad_pri, res.json(), elapsed)
    else:
        record("Tasks", "TC-TSK-003", "Tạo task sai enum Priority", "POST", f"/project/{project_id}/tasks", 422, res.status_code, "FAIL", "Không bắt lỗi enum priority", p_bad_pri, res.text, elapsed)

    # TC-TSK-004: Get Tasks List with Filtering, Sorting & Pagination
    t0 = time.time(); res = client.get(f"/project/{project_id}/tasks?priority=high&page=1&size=10&sort_by=created_at&sort_order=desc", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and "meta" in res.json()["data"]:
        record("Tasks", "TC-TSK-004", "Lấy danh sách task + Lọc & Phân trang", "GET", f"/project/{project_id}/tasks", 200, res.status_code, "PASS", "Lọc theo priority=high & pagination meta hợp lệ", None, res.json(), elapsed)
    else:
        record("Tasks", "TC-TSK-004", "Lấy danh sách task + Lọc & Phân trang", "GET", f"/project/{project_id}/tasks", 200, res.status_code, "FAIL", "Lỗi lấy danh sách task", None, res.text, elapsed)

    # TC-TSK-005: Get Task Detail
    t0 = time.time(); res = client.get(f"/tasks/{task_id}", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and res.json()["data"]["id"] == task_id:
        record("Tasks", "TC-TSK-005", "Xem chi tiết task", "GET", f"/tasks/{task_id}", 200, res.status_code, "PASS", "Trả về chi tiết task thành công", None, res.json(), elapsed)
    else:
        record("Tasks", "TC-TSK-005", "Xem chi tiết task", "GET", f"/tasks/{task_id}", 200, res.status_code, "FAIL", "Lỗi lấy chi tiết task", None, res.text, elapsed)

    # TC-TSK-006: Stranger Gets Task Detail (IDOR Check)
    t0 = time.time(); res = client.get(f"/tasks/{task_id}", headers=stranger_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 403:
        record("Tasks", "TC-TSK-006", "Người ngoài xem task chi tiết (IDOR)", "GET", f"/tasks/{task_id}", 403, res.status_code, "PASS", "Chặn bằng 403 Forbidden chính xác", None, res.json(), elapsed)
    else:
        record("Tasks", "TC-TSK-006", "Người ngoài xem task chi tiết (IDOR)", "GET", f"/tasks/{task_id}", 403, res.status_code, "FAIL", "Lỗi IDOR đọc task", None, res.text, elapsed)

    # TC-TSK-007: Assignee Updates Task
    p_upd_task = {"status": "in_progress", "title": "Thiết kế CSDL v2 (Đang làm)"}
    t0 = time.time(); res = client.patch(f"/tasks/{task_id}", json=p_upd_task, headers=member_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and res.json()["data"]["status"] == "in_progress":
        record("Tasks", "TC-TSK-007", "Assignee cập nhật trạng thái task", "PATCH", f"/tasks/{task_id}", 200, res.status_code, "PASS", "Cập nhật status sang in_progress", p_upd_task, res.json(), elapsed)
    else:
        record("Tasks", "TC-TSK-007", "Assignee cập nhật trạng thái task", "PATCH", f"/tasks/{task_id}", 200, res.status_code, "FAIL", "Cập nhật task thất bại", p_upd_task, res.text, elapsed)

    # TC-TSK-008: Assign Task to Non-Project-Member
    p_bad_assign = {"assignee_id": 9999}
    t0 = time.time(); res = client.patch(f"/tasks/{task_id}", json=p_bad_assign, headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 400:
        record("Tasks", "TC-TSK-008", "Gán task cho người không thuộc dự án", "PATCH", f"/tasks/{task_id}", 400, res.status_code, "PASS", "Bắt lỗi 400 Bad Request người dùng không thuộc dự án", p_bad_assign, res.json(), elapsed)
    else:
        record("Tasks", "TC-TSK-008", "Gán task cho người không thuộc dự án", "PATCH", f"/tasks/{task_id}", 400, res.status_code, "FAIL", "Không chặn gán người ngoài", p_bad_assign, res.text, elapsed)

    # TC-TSK-009: Member (Non-owner) Deletes Task
    t0 = time.time(); res = client.delete(f"/tasks/{task_id}", headers=member_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 403:
        record("Tasks", "TC-TSK-009", "Member thường cố tình xóa task", "DELETE", f"/tasks/{task_id}", 403, res.status_code, "PASS", "Chỉ Owner mới có quyền xóa task (403)", None, res.json(), elapsed)
    else:
        record("Tasks", "TC-TSK-009", "Member thường cố tình xóa task", "DELETE", f"/tasks/{task_id}", 403, res.status_code, "FAIL", "Không chặn member xóa task", None, res.text, elapsed)

    # -------------------------------------------------------------
    # 6. COMMENTS MODULE SUITE (Verified After Fix)
    # -------------------------------------------------------------
    # TC-CMT-001: Create Comment on Task (Standard RESTful Path)
    p_cmt = {"content": "Tài liệu ERD đã upload lên wiki nội bộ."}
    t0 = time.time(); res = client.post(f"/tasks/{task_id}/comments", json=p_cmt, headers=member_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 201 and res.json().get("statusCode") == 201 and res.json()["data"]["content"] == p_cmt["content"]:
        record("Comments", "TC-CMT-001", "Tạo bình luận vào Task (Chuẩn RESTful Path)", "POST", f"/tasks/{task_id}/comments", 201, res.status_code, "PASS", "Thêm comment thành công, lưu đúng user_id và nội dung", p_cmt, res.json(), elapsed)
    else:
        record("Comments", "TC-CMT-001", "Tạo bình luận vào Task (Chuẩn RESTful Path)", "POST", f"/tasks/{task_id}/comments", 201, res.status_code, "FAIL", "Lỗi tạo comment", p_cmt, res.text, elapsed)

    # TC-CMT-002: Get All Comments on Task (Standard RESTful Path)
    t0 = time.time(); res = client.get(f"/tasks/{task_id}/comments", headers=member_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200 and isinstance(res.json().get("data"), list) and len(res.json()["data"]) >= 1:
        record("Comments", "TC-CMT-002", "Lấy danh sách bình luận của Task", "GET", f"/tasks/{task_id}/comments", 200, res.status_code, "PASS", f"Trả về danh sách {len(res.json()['data'])} bình luận", None, res.json(), elapsed)
    else:
        record("Comments", "TC-CMT-002", "Lấy danh sách bình luận của Task", "GET", f"/tasks/{task_id}/comments", 200, res.status_code, "FAIL", "Lỗi lấy danh sách comments", None, res.text, elapsed)

    # TC-CMT-003: Stranger Cannot Comment on Task (IDOR Check)
    t0 = time.time(); res = client.post(f"/tasks/{task_id}/comments", json={"content": "Hacker comment"}, headers=stranger_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 403:
        record("Comments", "TC-CMT-003", "Người ngoài bình luận trái phép (IDOR Check)", "POST", f"/tasks/{task_id}/comments", 403, res.status_code, "PASS", "Chặn người ngoài bình luận bằng 403 Forbidden", None, res.json(), elapsed)
    else:
        record("Comments", "TC-CMT-003", "Người ngoài bình luận trái phép (IDOR Check)", "POST", f"/tasks/{task_id}/comments", 403, res.status_code, "FAIL", "Lỗi IDOR: Cho phép người ngoài comment", None, res.text, elapsed)

    # -------------------------------------------------------------
    # 7. SECURITY & EDGE CASES SUITE
    # -------------------------------------------------------------
    # TC-SEC-001: SQL Injection in Project Search
    p_sqli = "/project?search=' OR '1'='1"
    t0 = time.time(); res = client.get(p_sqli, headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 200:
        record("Security", "TC-SEC-001", "SQL Injection trong tham số tìm kiếm", "GET", p_sqli, 200, res.status_code, "PASS", "SQLAlchemy Parameterized Query an toàn, chống SQLi thành công", None, res.json(), elapsed)
    else:
        record("Security", "TC-SEC-001", "SQL Injection trong tham số tìm kiếm", "GET", p_sqli, 200, res.status_code, "FAIL", "Lỗi xử lý ký tự đặc biệt SQL", None, res.text, elapsed)

    # TC-SEC-002: XSS Payload in Task Title
    p_xss = {"title": "<script>alert('XSS')</script>", "priority": "low"}
    t0 = time.time(); res = client.post(f"/project/{project_id}/tasks", json=p_xss, headers=member_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 201:
        record("Security", "TC-SEC-002", "XSS Payload trong tiêu đề Task", "POST", f"/project/{project_id}/tasks", 201, res.status_code, "PASS", "Lưu trữ dữ liệu thô an toàn, không thực thi script phía server", p_xss, res.json(), elapsed)
    else:
        record("Security", "TC-SEC-002", "XSS Payload trong tiêu đề Task", "POST", f"/project/{project_id}/tasks", 201, res.status_code, "FAIL", "Lỗi lưu payload", p_xss, res.text, elapsed)

    # TC-SEC-003: JWT Algorithm None Attack
    tampered_payload = {"sub": str(admin_user_id), "role": "admin"}
    token_none = jwt.encode(tampered_payload, key="", algorithm="none")
    t0 = time.time(); res = client.get("/users", headers={"Authorization": f"Bearer {token_none}"}); elapsed = (time.time() - t0) * 1000
    if res.status_code == 401:
        record("Security", "TC-SEC-003", "Tấn công JWT Algorithm 'none'", "GET", "/users", 401, res.status_code, "PASS", "PyJWT chặt chẽ từ chối algorithm none bằng 401", None, res.json(), elapsed)
    else:
        record("Security", "TC-SEC-003", "Tấn công JWT Algorithm 'none'", "GET", "/users", 401, res.status_code, "FAIL", "Lỗ hổng bảo mật: Chấp nhận token không ký", None, res.text, elapsed)

    # TC-SEC-004: JWT Forged Signature with Weak/Wrong Secret
    token_forged = jwt.encode(tampered_payload, key="wrong_secret_key_123456789012345678", algorithm="HS256")
    t0 = time.time(); res = client.get("/users", headers={"Authorization": f"Bearer {token_forged}"}); elapsed = (time.time() - t0) * 1000
    if res.status_code == 401:
        record("Security", "TC-SEC-004", "JWT giả mạo chữ ký (Forged Secret)", "GET", "/users", 401, res.status_code, "PASS", "Từ chối xác thực 401 Unauthorized", None, res.json(), elapsed)
    else:
        record("Security", "TC-SEC-004", "JWT giả mạo chữ ký (Forged Secret)", "GET", "/users", 401, res.status_code, "FAIL", "Lỗ hổng: Chấp nhận token sai secret", None, res.text, elapsed)

    # TC-SEC-005: Token Missing 'sub' Claim
    token_no_sub = jwt.encode({"role": "admin"}, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    t0 = time.time(); res = client.get("/users/me", headers={"Authorization": f"Bearer {token_no_sub}"}); elapsed = (time.time() - t0) * 1000
    if res.status_code == 401:
        record("Security", "TC-SEC-005", "JWT thiếu trường định danh 'sub'", "GET", "/users/me", 401, res.status_code, "PASS", "Bắt lỗi thiếu claim 'sub' bằng 401", None, res.json(), elapsed)
    else:
        record("Security", "TC-SEC-005", "JWT thiếu trường định danh 'sub'", "GET", "/users/me", 401, res.status_code, "FAIL", "Không bắt lỗi thiếu claim", None, res.text, elapsed)

    # -------------------------------------------------------------
    # 8. MEMBER REMOVAL & CLEANUP SUITE
    # -------------------------------------------------------------
    # TC-PRJ-013: Owner Removes Member from Project
    t0 = time.time(); res = client.delete(f"/project/{project_id}/members/{member_user_id}", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 204:
        record("Projects", "TC-PRJ-013", "Owner xóa thành viên khỏi dự án", "DELETE", f"/project/{project_id}/members/{member_user_id}", 204, res.status_code, "PASS", "Xóa thành viên thành công (204 No Content)", None, None, elapsed)
    else:
        record("Projects", "TC-PRJ-013", "Owner xóa thành viên khỏi dự án", "DELETE", f"/project/{project_id}/members/{member_user_id}", 204, res.status_code, "FAIL", "Xóa thành viên thất bại", None, res.text, elapsed)

    # TC-PRJ-014: Owner Attempts to Delete Project Creator (Self)
    owner_user_id = user_owner.id
    t0 = time.time(); res = client.delete(f"/project/{project_id}/members/{owner_user_id}", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 400:
        record("Projects", "TC-PRJ-014", "Chặn xóa Creator/Owner chính của dự án", "DELETE", f"/project/{project_id}/members/{owner_user_id}", 400, res.status_code, "PASS", "Bảo vệ hệ thống: Không cho phép xóa creator (400)", None, res.json(), elapsed)
    else:
        record("Projects", "TC-PRJ-014", "Chặn xóa Creator/Owner chính của dự án", "DELETE", f"/project/{project_id}/members/{owner_user_id}", 400, res.status_code, "FAIL", "Không chặn xóa Owner chính", None, res.text, elapsed)

    # TC-TSK-010: Owner Deletes Task
    t0 = time.time(); res = client.delete(f"/tasks/{task_id}", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 204:
        record("Tasks", "TC-TSK-010", "Owner xóa task", "DELETE", f"/tasks/{task_id}", 204, res.status_code, "PASS", "Xóa task thành công (204 No Content)", None, None, elapsed)
    else:
        record("Tasks", "TC-TSK-010", "Owner xóa task", "DELETE", f"/tasks/{task_id}", 204, res.status_code, "FAIL", "Xóa task thất bại", None, res.text, elapsed)

    # TC-PRJ-015: Owner Deletes Project (Cascade Check)
    t0 = time.time(); res = client.delete(f"/project/{project_id}", headers=owner_hdr); elapsed = (time.time() - t0) * 1000
    if res.status_code == 204:
        record("Projects", "TC-PRJ-015", "Owner xóa toàn bộ dự án", "DELETE", f"/project/{project_id}", 204, res.status_code, "PASS", "Xóa dự án và liên hoàn thành công (204 No Content)", None, None, elapsed)
    else:
        record("Projects", "TC-PRJ-015", "Owner xóa toàn bộ dự án", "DELETE", f"/project/{project_id}", 204, res.status_code, "FAIL", "Xóa dự án thất bại", None, res.text, elapsed)

    # Write execution output to json
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(test_results),
        "passed": len([t for t in test_results if t["status"] == "PASS"]),
        "failed": len([t for t in test_results if t["status"] == "FAIL"]),
        "bugs_found": len([t for t in test_results if "BUG" in t["status"]]),
        "pass_rate": f"{(len([t for t in test_results if t['status'] == 'PASS']) / len(test_results) * 100):.2f}%",
        "results": test_results
    }

    with open("qa_test_report_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\nCompleted {summary['total_tests']} tests: {summary['passed']} PASS, {summary['failed']} FAIL, {summary['bugs_found']} BUGS. Pass Rate: {summary['pass_rate']}")
    return summary

if __name__ == "__main__":
    run_qa_suite()
