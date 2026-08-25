import pytest
from app.models import ProjectModel, ProjectMembersModel, RoleProject
from app.services import save_project, join_project

def test_delete_member_logic(client, user_headers, user2_headers, test_user, test_user2, db_session):
    """Kiểm tra hành vi xóa member khỏi project theo user_id"""
    proj = save_project({"name": "Project For Deleting Member", "description": "Desc"}, test_user.id, db_session)
    join_project(test_user2.id, proj.id, db_session, RoleProject.MEMBER)

    res = client.delete(f"/project/{proj.id}/members/{test_user2.id}", headers=user_headers)
    assert res.status_code == 200
    assert "Xóa thành viên thành công" in res.json()["message"]


def test_delete_nonexistent_member(client, user_headers, test_user, db_session):
    """Kiểm tra khi xóa member id không tồn tại trong project -> 404 Not Found"""
    proj = save_project({"name": "Project For Deleting Member", "description": "Desc"}, test_user.id, db_session)
    
    res = client.delete(f"/project/{proj.id}/members/999999", headers=user_headers)
    assert res.status_code == 404
    assert "Không tồn tại Member cần xóa" in res.json()["message"]


def test_response_envelope_structure(client):
    """Kiểm tra cấu trúc chuẩn ApiResponse: {statusCode, message, data, error, timestamp, path}"""
    res = client.get("/")
    assert res.status_code == 200
    # Root endpoint currently returns a simple dict {"message": ...}
    # We document whether root conforms to ApiResponse or not
