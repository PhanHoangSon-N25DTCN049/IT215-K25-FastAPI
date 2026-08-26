import pytest
from app.models import ActivityLogModel, RoleProject
from app.services import save_project, join_project


def test_activity_log_on_create_project(client, user_headers, test_user, db_session):
    """Khi tạo project mới, hệ thống tự động ghi activity log CREATE_PROJECT"""
    payload = {
        "name": "Dự án Activity Log",
        "description": "Thử nghiệm ghi log thao tác"
    }
    response = client.post("/project", json=payload, headers=user_headers)
    assert response.status_code == 201
    project_id = response.json()["data"]["id"]

    # Kiểm tra API lấy danh sách activities
    log_res = client.get(f"/project/{project_id}/activities", headers=user_headers)
    assert log_res.status_code == 200
    logs = log_res.json()["data"]
    assert len(logs) == 1
    assert logs[0]["action"] == "CREATE_PROJECT"
    assert logs[0]["project_id"] == project_id
    assert logs[0]["user_id"] == test_user.id
    assert logs[0]["user_name"] == test_user.full_name
    assert logs[0]["details"]["name"] == "Dự án Activity Log"


def test_activity_log_on_update_project(client, user_headers, test_user, db_session):
    """Khi cập nhật thông tin project, hệ thống ghi log UPDATE_PROJECT"""
    project = save_project({"name": "Project Gốc", "description": "Desc"}, test_user.id, db_session)

    update_payload = {"name": "Project Đã Đổi Tên", "description": "Desc Mới"}
    res = client.patch(f"/project/{project.id}", json=update_payload, headers=user_headers)
    assert res.status_code == 200

    log_res = client.get(f"/project/{project.id}/activities", headers=user_headers)
    assert log_res.status_code == 200
    logs = log_res.json()["data"]
    assert len(logs) == 1
    assert logs[0]["action"] == "UPDATE_PROJECT"
    assert logs[0]["details"]["name"] == "Project Đã Đổi Tên"
    assert logs[0]["details"]["description"] == "Desc Mới"


def test_activity_log_on_add_and_remove_member(client, user_headers, test_user, test_user2, db_session):
    """Khi thêm và xóa thành viên, hệ thống ghi log ADD_MEMBER và REMOVE_MEMBER"""
    project = save_project({"name": "Team Project", "description": "Desc"}, test_user.id, db_session)

    # 1. Thêm thành viên
    add_payload = {"user_id": test_user2.id, "role": "member"}
    add_res = client.post(f"/project/{project.id}/member", json=add_payload, headers=user_headers)
    assert add_res.status_code == 201

    # 2. Xóa thành viên
    del_res = client.delete(f"/project/{project.id}/members/{test_user2.id}", headers=user_headers)
    assert del_res.status_code == 204

    # 3. Kiểm tra log
    log_res = client.get(f"/project/{project.id}/activities", headers=user_headers)
    assert log_res.status_code == 200
    logs = log_res.json()["data"]
    assert len(logs) == 2

    # Vì sắp xếp desc theo created_at/id nên log mới nhất là REMOVE_MEMBER
    assert logs[0]["action"] == "REMOVE_MEMBER"
    assert logs[0]["details"]["target_user_id"] == test_user2.id

    assert logs[1]["action"] == "ADD_MEMBER"
    assert logs[1]["details"]["target_user_id"] == test_user2.id
    assert logs[1]["details"]["role"] == "member"


def test_activity_logs_permissions(client, user_headers, user2_headers, test_user, test_user2, db_session):
    """Chỉ thành viên thuộc project mới có quyền xem activity logs; người ngoài bị chặn 403"""
    project = save_project({"name": "Secret Project", "description": "Desc"}, test_user.id, db_session)

    # Người ngoài (user2) truy cập -> 403 Forbidden
    res_forbidden = client.get(f"/project/{project.id}/activities", headers=user2_headers)
    assert res_forbidden.status_code == 403

    # Thêm user2 làm member
    join_project(test_user2.id, project.id, db_session, role=RoleProject.MEMBER)

    # Sau khi là member -> 200 OK
    res_allowed = client.get(f"/project/{project.id}/activities", headers=user2_headers)
    assert res_allowed.status_code == 200


def test_activity_logs_pagination(client, user_headers, test_user, db_session):
    """Kiểm tra tính năng phân trang (limit, offset) của activity logs"""
    project = save_project({"name": "Paged Project", "description": "Desc"}, test_user.id, db_session)

    # Tạo 5 updates
    for i in range(5):
        client.patch(f"/project/{project.id}", json={"name": f"Name Update {i}"}, headers=user_headers)

    # Lấy page 1 với limit = 2
    res_p1 = client.get(f"/project/{project.id}/activities?limit=2&offset=0", headers=user_headers)
    assert res_p1.status_code == 200
    logs_p1 = res_p1.json()["data"]
    assert len(logs_p1) == 2
    assert logs_p1[0]["details"]["name"] == "Name Update 4"
    assert logs_p1[1]["details"]["name"] == "Name Update 3"

    # Lấy page 2 với limit = 2 & offset = 2
    res_p2 = client.get(f"/project/{project.id}/activities?limit=2&offset=2", headers=user_headers)
    assert res_p2.status_code == 200
    logs_p2 = res_p2.json()["data"]
    assert len(logs_p2) == 2
    assert logs_p2[0]["details"]["name"] == "Name Update 2"
    assert logs_p2[1]["details"]["name"] == "Name Update 1"
