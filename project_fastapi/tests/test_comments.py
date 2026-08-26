import pytest
from app.models import RoleProject
from app.services import save_project, join_project, create_task

@pytest.fixture
def project_with_task(db_session, test_user):
    proj = save_project({"name": "Comment Test Project", "description": "Desc"}, test_user.id, db_session)
    task = create_task({
        "project_id": proj.id,
        "title": "Task for Comments",
        "description": "Desc",
        "assignee_id": test_user.id,
        "priority": "medium",
    }, db_session)
    return proj, task

def test_create_comment_on_task_success(client, user_headers, project_with_task, test_user):
    proj, task = project_with_task
    payload = {"content": "This is an important update for the task."}
    res = client.post(f"/tasks/{task.id}/comments", json=payload, headers=user_headers)
    assert res.status_code == 201
    body = res.json()
    assert body["statusCode"] == 201
    assert body["data"]["content"] == payload["content"]
    assert body["data"]["task_id"] == task.id
    assert body["data"]["user_id"] == test_user.id

def test_get_all_comments_on_task_success(client, user_headers, project_with_task):
    proj, task = project_with_task
    # Add a comment first
    client.post(f"/tasks/{task.id}/comments", json={"content": "Comment 1"}, headers=user_headers)
    client.post(f"/tasks/{task.id}/comments", json={"content": "Comment 2"}, headers=user_headers)
    
    res = client.get(f"/tasks/{task.id}/comments", headers=user_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["statusCode"] == 200
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 2
    assert body["data"][0]["content"] == "Comment 1"
    assert body["data"][1]["content"] == "Comment 2"

def test_non_member_cannot_comment(client, user2_headers, project_with_task):
    proj, task = project_with_task
    res = client.post(f"/tasks/{task.id}/comments", json={"content": "Hacker comment"}, headers=user2_headers)
    assert res.status_code == 403

def test_non_member_cannot_get_comments(client, user2_headers, project_with_task):
    proj, task = project_with_task
    res = client.get(f"/tasks/{task.id}/comments", headers=user2_headers)
    assert res.status_code == 403

def test_comment_on_nonexistent_task(client, user_headers):
    res = client.post("/tasks/999999/comments", json={"content": "Test"}, headers=user_headers)
    assert res.status_code == 404

def test_comment_validation_empty_content(client, user_headers, project_with_task):
    proj, task = project_with_task
    res = client.post(f"/tasks/{task.id}/comments", json={}, headers=user_headers)
    assert res.status_code == 422
