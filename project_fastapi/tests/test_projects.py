import pytest
from app.models import ProjectModel, ProjectMembersModel, RoleProject
from app.services import save_project, join_project

def test_create_project_success(client, user_headers, test_user, db_session):
    """Tạo dự án mới thành công -> 201 Created"""
    payload = {
        "name": "Dự án Alpha",
        "description": "Mô tả dự án Alpha"
    }
    response = client.post("/project", json=payload, headers=user_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["statusCode"] == 201
    assert data["data"]["name"] == "Dự án Alpha"
    assert data["data"]["description"] == "Mô tả dự án Alpha"
    assert data["data"]["owner_id"] == test_user.id
    assert data["data"]["role_user"] == "owner"


def test_create_project_unauthorized(client):
    """Tạo dự án không có token -> 401/403"""
    response = client.post("/project", json={"name": "No Auth"})
    assert response.status_code in [401, 403]


def test_create_project_missing_name(client, user_headers):
    """Tạo dự án thiếu tên -> 422 Unprocessable Entity"""
    response = client.post("/project", json={"description": "No Name"}, headers=user_headers)
    assert response.status_code == 422


def test_get_projects_list(client, user_headers, user2_headers, test_user, test_user2, db_session):
    """Lấy danh sách dự án của người dùng hiện tại (chỉ dự án mình tham gia) -> 200 OK"""
    # Create project 1 for user 1
    proj1 = save_project({"name": "Project 1", "description": "Desc 1"}, test_user.id, db_session)
    # Create project 2 for user 2
    proj2 = save_project({"name": "Project 2", "description": "Desc 2"}, test_user2.id, db_session)

    # User 1 queries projects
    res1 = client.get("/project", headers=user_headers)
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert len(data1) == 1
    assert data1[0]["name"] == "Project 1"

    # User 2 queries projects
    res2 = client.get("/project", headers=user2_headers)
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert len(data2) == 1
    assert data2[0]["name"] == "Project 2"


def test_get_projects_search(client, user_headers, test_user, db_session):
    """Tìm kiếm dự án theo từ khóa search -> 200 OK"""
    save_project({"name": "Backend Nodejs", "description": "Desc"}, test_user.id, db_session)

    res = client.get("/project?search=Nodejs", headers=user_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Backend Nodejs"

    res_empty = client.get("/project?search=React", headers=user_headers)
    assert res_empty.status_code == 200
    assert len(res_empty.json()["data"]) == 0


def test_get_project_detail_as_owner(client, user_headers, test_user, db_session):
    """Lấy chi tiết dự án với tư cách Owner -> 200 OK, role_user=owner"""
    proj = save_project({"name": "Detail Project", "description": "Detail"}, test_user.id, db_session)

    res = client.get(f"/project/{proj.id}", headers=user_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == proj.id
    assert data["role_user"] == "owner"


def test_get_project_detail_as_non_member(client, user2_headers, test_user, db_session):
    """Lấy chi tiết dự án không phải thành viên -> 403 Forbidden"""
    proj = save_project({"name": "Secret Project", "description": "Secret"}, test_user.id, db_session)

    res = client.get(f"/project/{proj.id}", headers=user2_headers)
    assert res.status_code == 403
    data = res.json()
    assert data["statusCode"] == 403
    assert "Bạn không có quyền truy cập dự án này" in data["message"]


def test_get_project_detail_not_found(client, user_headers):
    """Lấy chi tiết dự án không tồn tại -> 404 Not Found"""
    res = client.get("/project/999999", headers=user_headers)
    assert res.status_code == 404
    data = res.json()
    assert data["statusCode"] == 404
    assert "Dự án không tồn tại" in data["message"]


def test_add_member_as_owner(client, user_headers, test_user, test_user2, db_session):
    """Owner thêm thành viên mới vào dự án -> 200/201"""
    proj = save_project({"name": "Team Project", "description": "Team"}, test_user.id, db_session)

    payload = {
        "user_id": test_user2.id,
        "role": "member"
    }
    res = client.post(f"/project/{proj.id}/member", json=payload, headers=user_headers)
    assert res.status_code in [200, 201]
    data = res.json()["data"]
    assert data["user_id"] == test_user2.id
    assert data["project_id"] == proj.id
    assert data["role"] == "member"


def test_add_member_as_non_owner(client, user2_headers, test_user, test_user2, db_session):
    """Member không phải Owner thêm thành viên -> 403 Forbidden"""
    proj = save_project({"name": "Team Project 2", "description": "Team"}, test_user.id, db_session)
    join_project(test_user2.id, proj.id, db_session, RoleProject.MEMBER)

    payload = {
        "user_id": test_user.id,
        "role": "member"
    }
    res = client.post(f"/project/{proj.id}/member", json=payload, headers=user2_headers)
    assert res.status_code == 403


def test_update_project_as_owner(client, user_headers, test_user, db_session):
    """Owner cập nhật thông tin dự án -> 200 OK"""
    proj = save_project({"name": "Old Project Name", "description": "Old Desc"}, test_user.id, db_session)

    payload = {
        "name": "Updated Project Name",
        "description": "Updated Desc"
    }
    res = client.patch(f"/project/{proj.id}", json=payload, headers=user_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["name"] == "Updated Project Name"
    assert data["description"] == "Updated Desc"


def test_update_project_as_non_owner(client, user2_headers, test_user, test_user2, db_session):
    """Member không phải Owner cập nhật dự án -> 403 Forbidden"""
    proj = save_project({"name": "Original Name", "description": "Original Desc"}, test_user.id, db_session)
    join_project(test_user2.id, proj.id, db_session, RoleProject.MEMBER)

    payload = {"name": "Hacked Name"}
    res = client.patch(f"/project/{proj.id}", json=payload, headers=user2_headers)
    assert res.status_code == 403
    assert "Bạn không có quyền sửa đổi dự án" in res.json()["message"]


def test_delete_project_as_owner(client, user_headers, test_user, db_session):
    """Owner xóa dự án -> 204 No Content"""
    proj = save_project({"name": "To Delete", "description": "Delete"}, test_user.id, db_session)

    res = client.delete(f"/project/{proj.id}", headers=user_headers)
    assert res.status_code == 204

    # Verify deleted via API
    check_res = client.get(f"/project/{proj.id}", headers=user_headers)
    assert check_res.status_code == 404

    # Verify soft deleted in database (data is preserved, not permanently deleted)
    db_proj = db_session.query(ProjectModel).filter(ProjectModel.id == proj.id).first()
    assert db_proj is not None
    assert db_proj.is_delete is True




def test_delete_project_as_non_owner(client, user2_headers, test_user, test_user2, db_session):
    """Member không phải Owner xóa dự án -> 403 Forbidden"""
    proj = save_project({"name": "Safe Project", "description": "Safe"}, test_user.id, db_session)
    join_project(test_user2.id, proj.id, db_session, RoleProject.MEMBER)

    res = client.delete(f"/project/{proj.id}", headers=user2_headers)
    assert res.status_code == 403
    assert "Bạn không có quyền xóa dự án" in res.json()["message"]


def test_delete_member_as_owner(client, user_headers, test_user, test_user2, db_session):
    """Owner xóa thành viên khỏi dự án -> 204 No Content"""
    proj = save_project({"name": "Team Delete", "description": "Desc"}, test_user.id, db_session)
    join_project(test_user2.id, proj.id, db_session, RoleProject.MEMBER)

    res = client.delete(f"/project/{proj.id}/members/{test_user2.id}", headers=user_headers)
    assert res.status_code == 204


def test_delete_member_as_non_owner(client, user2_headers, test_user, test_user2, db_session):
    """Member không phải Owner xóa thành viên khác -> 403 Forbidden"""
    proj = save_project({"name": "Team Delete 2", "description": "Desc"}, test_user.id, db_session)
    join_project(test_user2.id, proj.id, db_session, RoleProject.MEMBER)

    res = client.delete(f"/project/{proj.id}/members/{test_user.id}", headers=user2_headers)
    assert res.status_code == 403
    assert "Bạn không có quyền thực hiện hành động này" in res.json()["message"]


def test_delete_member_not_found(client, user_headers, test_user, db_session):
    """Owner xóa thành viên không tồn tại trong dự án -> 404 Not Found"""
    proj = save_project({"name": "Team Delete 3", "description": "Desc"}, test_user.id, db_session)

    res = client.delete(f"/project/{proj.id}/members/999999", headers=user_headers)
    assert res.status_code == 404
    assert "Không tồn tại Member cần xóa" in res.json()["message"]

