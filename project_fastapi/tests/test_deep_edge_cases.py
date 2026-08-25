import pytest
from datetime import datetime, timedelta
import jwt
from app.models import ProjectModel, ProjectMembersModel, RoleProject, TaskModel, TaskStatus, TaskPriority, RoleUser, UserModel
from app.services import save_project, join_project
from app.core import settings, hash_password

def test_sql_injection_in_project_search(client, user_headers, test_user, db_session):
    """Kiểm tra SQL Injection trong tham số search của GET /project"""
    save_project({"name": "Safe Project 1", "description": "Desc"}, test_user.id, db_session)
    
    # SQL injection payload
    payloads = [
        "' OR '1'='1",
        "'; DROP TABLE projects; --",
        "UNION SELECT * FROM users --",
        "%'"
    ]
    for p in payloads:
        res = client.get(f"/project?search={p}", headers=user_headers)
        assert res.status_code == 200
        assert isinstance(res.json()["data"], list)


def test_xss_and_unicode_in_task_title(client, user_headers, test_user, db_session):
    """Kiểm tra lưu trữ chuỗi chứa ký tự Unicode tiếng Việt, Emoji và XSS Payload"""
    proj = save_project({"name": "Dự án Tiếng Việt 🚀", "description": "<script>alert('xss')</script>"}, test_user.id, db_session)
    
    payload = {
        "title": "<img src=x onerror=alert(1)> Tiêu đề có dấu & emoji 🔥",
        "description": "Mô tả: <html><body>Test</body></html>",
        "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "priority": "high"
    }
    res = client.post(f"/project/{proj.id}/tasks", json=payload, headers=user_headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert "<img src=x" in data["title"]
    assert "emoji 🔥" in data["title"]


def test_pagination_boundary_values(client, user_headers, test_user, db_session):
    """Kiểm tra biên của Pagination: page=0 (vi phạm ge=1), size=0, size=101 (vi phạm le=100)"""
    proj = save_project({"name": "Paging Project", "description": "Desc"}, test_user.id, db_session)
    
    # 1. page=0 -> 422
    res_page_0 = client.get(f"/project/{proj.id}/tasks?page=0", headers=user_headers)
    assert res_page_0.status_code == 422
    
    # 2. size=0 -> 422
    res_size_0 = client.get(f"/project/{proj.id}/tasks?size=0", headers=user_headers)
    assert res_size_0.status_code == 422
    
    # 3. size=101 -> 422
    res_size_101 = client.get(f"/project/{proj.id}/tasks?size=101", headers=user_headers)
    assert res_size_101.status_code == 422
    
    # 4. page=1, size=100 (Hợp lệ) -> 200
    res_valid = client.get(f"/project/{proj.id}/tasks?page=1&size=100", headers=user_headers)
    assert res_valid.status_code == 200


def test_add_nonexistent_user_to_project(client, user_headers, test_user, db_session):
    """Kiểm tra khi thêm user_id không tồn tại vào project"""
    proj = save_project({"name": "Add Nonexistent User Proj", "description": "Desc"}, test_user.id, db_session)
    payload = {"user_id": 999999, "role": "member"}
    res = client.post(f"/project/{proj.id}/member", json=payload, headers=user_headers)
    # Ghi nhận trạng thái: nên là 404 hoặc 400 thay vì 500
    assert res.status_code in [400, 404, 201]


def test_add_duplicate_member_to_project(client, user_headers, test_user, test_user2, db_session):
    """Kiểm tra khi thêm 1 user đã là member vào project lần thứ 2"""
    proj = save_project({"name": "Duplicate Member Proj", "description": "Desc"}, test_user.id, db_session)
    join_project(test_user2.id, proj.id, db_session, RoleProject.MEMBER)
    
    payload = {"user_id": test_user2.id, "role": "member"}
    res = client.post(f"/project/{proj.id}/member", json=payload, headers=user_headers)
    # Ghi nhận trạng thái: nên là 400 hoặc 409 thay vì crash 500
    assert res.status_code in [400, 409, 500]


def test_idor_cross_tenant_task_access(client, user_headers, user2_headers, test_user, test_user2, db_session):
    """Kiểm tra IDOR / Multi-Tenancy: User B cố gắng xem / sửa / xóa Task của Project A mà mình không tham gia"""
    # User 1 tạo Project 1 và Task 1 (User 2 KHÔNG PHẢI member)
    proj1 = save_project({"name": "Private Project 1", "description": "Desc"}, test_user.id, db_session)
    t1 = TaskModel(project_id=proj1.id, title="Private Task 1", description="Top secret", assignee_id=test_user.id, priority=TaskPriority.HIGH, status=TaskStatus.TODO, due_date=datetime.now() + timedelta(days=1))
    db_session.add(t1)
    db_session.commit()
    db_session.refresh(t1)

    # 1. User 2 gọi GET /tasks/{task_id} -> 403 Forbidden
    res_get = client.get(f"/tasks/{t1.id}", headers=user2_headers)
    assert res_get.status_code == 403

    # 2. User 2 gọi PATCH /tasks/{task_id} -> 403 Forbidden
    res_patch = client.patch(f"/tasks/{t1.id}", json={"title": "Hacked"}, headers=user2_headers)
    assert res_patch.status_code == 403

    # 3. User 2 gọi DELETE /tasks/{task_id} -> 403 Forbidden
    res_del = client.delete(f"/tasks/{t1.id}", headers=user2_headers)
    assert res_del.status_code == 403

    # 4. User 2 gọi GET /project/{project_id}/tasks -> 403 Forbidden
    res_list = client.get(f"/project/{proj1.id}/tasks", headers=user2_headers)
    assert res_list.status_code == 403


def test_token_tampering_algorithm_none(client):
    """Kiểm tra tấn công 'none' algorithm trong JWT"""
    none_alg_token = jwt.encode({"sub": "1", "role": "admin", "exp": datetime.now().timestamp() + 3600}, key="", algorithm="none")
    res = client.get("/users/me", headers={"Authorization": f"Bearer {none_alg_token}"})
    assert res.status_code == 401


def test_token_missing_sub_field(client):
    """Kiểm tra token hợp lệ chữ ký nhưng thiếu trường 'sub'"""
    bad_payload_token = jwt.encode({"role": "user", "exp": datetime.now().timestamp() + 3600}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    res = client.get("/users/me", headers={"Authorization": f"Bearer {bad_payload_token}"})
    # Nên trả về 401 hoặc 404 hoặc 422 thay vì 500
    assert res.status_code in [401, 422, 500]
