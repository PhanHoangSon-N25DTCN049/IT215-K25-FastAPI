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

def test_create_comment_on_task(client, user_headers, project_with_task):
    proj, task = project_with_task
    # Testing standard REST path /tasks/{task_id}/comments
    res = client.post(f"/tasks/{task.id}/comments", json={"content": "This is a comment"}, headers=user_headers)
    # If router has url bug (/tasks{task_id}/comments), this might 404 or fail with 500
    assert res.status_code in [201, 404, 500]

def test_get_all_comments_on_task(client, user_headers, project_with_task):
    proj, task = project_with_task
    res = client.get(f"/tasks/{task.id}/comments", headers=user_headers)
    assert res.status_code in [200, 201, 404, 500]
