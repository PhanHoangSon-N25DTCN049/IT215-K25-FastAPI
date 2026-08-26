import pytest
from datetime import datetime, timedelta
from app.models import ProjectModel, ProjectMembersModel, RoleProject, TaskModel, TaskStatus, TaskPriority
from app.services import save_project, join_project, create_task

@pytest.fixture
def test_project_with_members(db_session, test_user, test_user2):
    # test_user is OWNER
    proj = save_project({"name": "Task Test Project", "description": "Project for Task Tests"}, test_user.id, db_session)
    # test_user2 is MEMBER
    join_project(test_user2.id, proj.id, db_session, RoleProject.MEMBER)
    return proj


def test_create_task_as_owner(client, user_headers, test_project_with_members):
    """Owner tạo task mới -> 201 Created"""
    payload = {
        "title": "Task 1 by Owner",
        "description": "Description 1",
        "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
        "priority": "high"
    }
    res = client.post(f"/project/{test_project_with_members.id}/tasks", json=payload, headers=user_headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["title"] == "Task 1 by Owner"
    assert data["project_id"] == test_project_with_members.id
    assert data["priority"] == "high"
    assert data["status"] == "todo"


def test_create_task_as_member(client, user2_headers, test_project_with_members):
    """Member tạo task mới -> 201 Created"""
    payload = {
        "title": "Task 2 by Member",
        "description": "Description 2",
        "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
        "priority": "medium"
    }
    res = client.post(f"/project/{test_project_with_members.id}/tasks", json=payload, headers=user2_headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["title"] == "Task 2 by Member"


def test_create_task_non_member(client, admin_headers, test_project_with_members):
    """User không thuộc project (admin) tạo task -> 403 Forbidden"""
    payload = {
        "title": "Task 3 by Outsider",
        "description": "Desc",
        "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "priority": "low"
    }
    res = client.post(f"/project/{test_project_with_members.id}/tasks", json=payload, headers=admin_headers)
    assert res.status_code == 403


def test_create_task_nonexistent_project(client, user_headers):
    """Tạo task trên project không tồn tại -> 404 Not Found"""
    payload = {
        "title": "Task on void",
        "description": "Desc",
        "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "priority": "low"
    }
    res = client.post("/project/999999/tasks", json=payload, headers=user_headers)
    assert res.status_code == 404


def test_create_task_invalid_priority(client, user_headers, test_project_with_members):
    """Tạo task với priority không hợp lệ -> 422 Unprocessable Entity"""
    payload = {
        "title": "Invalid Priority Task",
        "description": "Desc",
        "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "priority": "URGENT_NOT_EXIST"
    }
    res = client.post(f"/project/{test_project_with_members.id}/tasks", json=payload, headers=user_headers)
    assert res.status_code == 422


def test_get_all_tasks_with_filters_and_pagination(client, user_headers, test_project_with_members, test_user, test_user2, db_session):
    """Lấy danh sách task với bộ lọc priority, status, pagination"""
    # Create 3 tasks
    t1 = TaskModel(project_id=test_project_with_members.id, title="Alpha Bug", description="Fix it", assignee_id=test_user.id, priority=TaskPriority.HIGH, status=TaskStatus.TODO, due_date=datetime.now() + timedelta(days=1))
    t2 = TaskModel(project_id=test_project_with_members.id, title="Beta Feature", description="Code it", assignee_id=test_user2.id, priority=TaskPriority.LOW, status=TaskStatus.IN_PROGRESS, due_date=datetime.now() + timedelta(days=3))
    t3 = TaskModel(project_id=test_project_with_members.id, title="Alpha Docs", description="Write it", assignee_id=test_user.id, priority=TaskPriority.HIGH, status=TaskStatus.DONE, due_date=datetime.now() + timedelta(days=5))
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    # 1. Filter title=Alpha
    res = client.get(f"/project/{test_project_with_members.id}/tasks?title=Alpha", headers=user_headers)
    assert res.status_code == 200
    res_data = res.json()["data"]
    assert len(res_data["data"]) == 2

    # 2. Filter priority=high
    res_pri = client.get(f"/project/{test_project_with_members.id}/tasks?priority=high", headers=user_headers)
    assert res_pri.status_code == 200
    assert len(res_pri.json()["data"]["data"]) == 2

    # 3. Filter status=in_progress
    res_st = client.get(f"/project/{test_project_with_members.id}/tasks?status=in_progress", headers=user_headers)
    assert res_st.status_code == 200
    assert len(res_st.json()["data"]["data"]) == 1
    assert res_st.json()["data"]["data"][0]["title"] == "Beta Feature"

    # 4. Pagination page=1, size=2
    res_page = client.get(f"/project/{test_project_with_members.id}/tasks?page=1&size=2", headers=user_headers)
    assert res_page.status_code == 200
    meta = res_page.json()["data"]["meta"]
    assert meta["current_page"] == 1
    assert meta["page_size"] == 2
    assert meta["total_items"] == 3
    assert meta["total_pages"] == 2
    assert len(res_page.json()["data"]["data"]) == 2


def test_get_task_detail(client, user_headers, user2_headers, test_project_with_members, test_user, db_session):
    """Lấy chi tiết task"""
    t = TaskModel(project_id=test_project_with_members.id, title="Detail Task", description="Detail Desc", assignee_id=test_user.id, priority=TaskPriority.MEDIUM, status=TaskStatus.TODO, due_date=datetime.now() + timedelta(days=2))
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    # Member can view
    res = client.get(f"/tasks/{t.id}", headers=user2_headers)
    assert res.status_code == 200
    assert res.json()["data"]["title"] == "Detail Task"

    # Nonexistent task -> 404
    res_404 = client.get("/tasks/999999", headers=user_headers)
    assert res_404.status_code == 404


def test_update_task_as_assignee(client, user2_headers, test_project_with_members, test_user2, db_session):
    """Assignee cập nhật task của mình -> 200 OK"""
    t = TaskModel(project_id=test_project_with_members.id, title="Assignee Task", description="Initial", assignee_id=test_user2.id, priority=TaskPriority.LOW, status=TaskStatus.TODO, due_date=datetime.now() + timedelta(days=2))
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    payload = {"status": "in_progress", "title": "Updated by Assignee"}
    res = client.patch(f"/tasks/{t.id}", json=payload, headers=user2_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == "in_progress"
    assert data["title"] == "Updated by Assignee"


def test_update_task_as_owner(client, user_headers, test_project_with_members, test_user2, db_session):
    """Owner cập nhật task được giao cho người khác -> 200 OK"""
    t = TaskModel(project_id=test_project_with_members.id, title="Task Assigned to User2", description="Initial", assignee_id=test_user2.id, priority=TaskPriority.LOW, status=TaskStatus.TODO, due_date=datetime.now() + timedelta(days=2))
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    payload = {"priority": "high"}
    res = client.patch(f"/tasks/{t.id}", json=payload, headers=user_headers)
    assert res.status_code == 200
    assert res.json()["data"]["priority"] == "high"


def test_update_task_as_unauthorized_member(client, user2_headers, test_project_with_members, test_user, db_session):
    """Member không phải Owner và không phải Assignee cập nhật task -> 403 Forbidden"""
    t = TaskModel(project_id=test_project_with_members.id, title="Owner's Task", description="Initial", assignee_id=test_user.id, priority=TaskPriority.LOW, status=TaskStatus.TODO, due_date=datetime.now() + timedelta(days=2))
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    payload = {"title": "Hacked Title"}
    res = client.patch(f"/tasks/{t.id}", json=payload, headers=user2_headers)
    assert res.status_code == 403
    assert "Bạn không có quyền chỉnh sửa task này" in res.json()["message"]


def test_update_task_assign_to_non_member(client, user_headers, test_project_with_members, test_admin, test_user, db_session):
    """Gán task cho người không thuộc project -> 400 Bad Request"""
    t = TaskModel(project_id=test_project_with_members.id, title="Task to Reassign", description="Initial", assignee_id=test_user.id, priority=TaskPriority.LOW, status=TaskStatus.TODO, due_date=datetime.now() + timedelta(days=2))
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    # test_admin is not a member of test_project_with_members
    payload = {"assignee_id": test_admin.id}
    res = client.patch(f"/tasks/{t.id}", json=payload, headers=user_headers)
    assert res.status_code == 400
    assert "Người dùng này không phải là thành viên" in res.json()["message"]


def test_delete_task_as_owner(client, user_headers, test_project_with_members, test_user, db_session):
    """Owner xóa task -> 204 No Content"""
    t = TaskModel(project_id=test_project_with_members.id, title="Task to Delete", description="Initial", assignee_id=test_user.id, priority=TaskPriority.LOW, status=TaskStatus.TODO, due_date=datetime.now() + timedelta(days=2))
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    res = client.delete(f"/tasks/{t.id}", headers=user_headers)
    assert res.status_code == 204

    # Verify deleted
    res_check = client.get(f"/tasks/{t.id}", headers=user_headers)
    assert res_check.status_code == 404


def test_delete_task_as_non_owner(client, user2_headers, test_project_with_members, test_user2, db_session):
    """Assignee/Member thường xóa task -> 403 Forbidden"""
    t = TaskModel(project_id=test_project_with_members.id, title="Task Safe from Non-Owner", description="Initial", assignee_id=test_user2.id, priority=TaskPriority.LOW, status=TaskStatus.TODO, due_date=datetime.now() + timedelta(days=2))
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    res = client.delete(f"/tasks/{t.id}", headers=user2_headers)
    assert res.status_code == 403
    assert "Bạn không có quyền xóa task này" in res.json()["message"]


def test_delete_task_with_comments_as_owner(client, user_headers, user2_headers, test_project_with_members, test_user, db_session):
    """Owner xóa Task ĐÃ CÓ COMMENTS -> Xóa thành công 204 No Content và tự động cascade delete comments"""
    # 1. Tạo task bởi Owner
    t = TaskModel(
        project_id=test_project_with_members.id,
        title="Task with multiple comments",
        description="Task to be deleted with comments",
        assignee_id=test_user.id,
        priority=TaskPriority.HIGH,
        status=TaskStatus.TODO,
        due_date=datetime.now() + timedelta(days=3)
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    # 2. Thêm 2 comments vào task (1 bởi Owner, 1 bởi Member)
    res_c1 = client.post(f"/tasks/{t.id}/comments", json={"content": "Comment 1 from Owner"}, headers=user_headers)
    assert res_c1.status_code == 201

    res_c2 = client.post(f"/tasks/{t.id}/comments", json={"content": "Comment 2 from Member"}, headers=user2_headers)
    assert res_c2.status_code == 201

    # 3. Kiểm tra danh sách comment trước khi xóa
    res_list_before = client.get(f"/tasks/{t.id}/comments", headers=user_headers)
    assert res_list_before.status_code == 200
    assert len(res_list_before.json()["data"]) == 2

    # 4. Owner tiến hành xóa task
    res_delete = client.delete(f"/tasks/{t.id}", headers=user_headers)
    assert res_delete.status_code == 204

    # 5. Xác minh Task đã bị xóa khỏi hệ thống -> 404 Not Found
    res_get_task = client.get(f"/tasks/{t.id}", headers=user_headers)
    assert res_get_task.status_code == 404

    # 6. Xác minh Endpoint Comments của task đã xóa trả về 404 Not Found
    res_get_comments = client.get(f"/tasks/{t.id}/comments", headers=user_headers)
    assert res_get_comments.status_code == 404


def test_update_task_assignee_zero_validation(client, user_headers, test_project_with_members, test_user, db_session):
    """Cập nhật task với assignee_id = 0 -> 422 Unprocessable Entity"""
    t = TaskModel(
        project_id=test_project_with_members.id,
        title="Zero Assignee Task",
        description="Initial",
        assignee_id=test_user.id,
        priority=TaskPriority.LOW,
        status=TaskStatus.TODO,
        due_date=datetime.now() + timedelta(days=2)
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    payload = {"assignee_id": 0}
    res = client.patch(f"/tasks/{t.id}", json=payload, headers=user_headers)
    assert res.status_code == 422


