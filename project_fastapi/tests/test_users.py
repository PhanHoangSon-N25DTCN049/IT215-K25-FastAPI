import pytest
from datetime import datetime
import jwt
from app.core import settings

def test_get_me_success(client, test_user, user_headers):
    """Lấy thông tin cá nhân của người dùng hiện tại -> 200 OK"""
    response = client.get("/users/me", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["statusCode"] == 200
    assert data["message"] == "Lấy thông tin thành công"
    assert data["data"]["id"] == test_user.id
    assert data["data"]["email"] == test_user.email
    assert data["data"]["full_name"] == test_user.full_name
    assert data["data"]["role"] == "user"


def test_get_me_unauthorized_no_token(client):
    """Lấy thông tin cá nhân không truyền token -> 401 / 403 HTTPBearer error"""
    response = client.get("/users/me")
    assert response.status_code in [401, 403]


def test_get_me_expired_token(client, test_user):
    """Lấy thông tin cá nhân với token hết hạn -> 401 Unauthorized"""
    expired_payload = {
        "sub": str(test_user.id),
        "role": str(test_user.role),
        "exp": datetime.now().timestamp() - 3600
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    response = client.get("/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    data = response.json()
    assert data["statusCode"] == 401
    assert "Token đã hết hạn" in data["message"]


def test_get_me_invalid_token(client):
    """Lấy thông tin cá nhân với token không hợp lệ -> 401 Unauthorized"""
    invalid_token = jwt.encode(
        {"sub": "1", "role": "user", "exp": datetime.now().timestamp() + 3600},
        "wrong_secret_key",
        algorithm="HS256"
    )
    response = client.get("/users/me", headers={"Authorization": f"Bearer {invalid_token}"})
    assert response.status_code == 401
    data = response.json()
    assert data["statusCode"] == 401
    assert "Không thể xác thực thông tin" in data["message"]


def test_admin_get_users_list(client, admin_headers, test_admin, test_user, test_inactive_user):
    """Admin lấy danh sách toàn bộ người dùng -> 200 OK"""
    response = client.get("/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["statusCode"] == 200
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 3


def test_admin_filter_users_by_email(client, admin_headers, test_user):
    """Admin lọc người dùng theo email -> 200 OK"""
    response = client.get(f"/users?email={test_user.email}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["email"] == test_user.email


def test_admin_filter_users_by_name(client, admin_headers, test_user):
    """Admin lọc người dùng theo tên -> 200 OK"""
    response = client.get(f"/users?name=Regular", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == test_user.id


def test_admin_filter_users_by_status(client, admin_headers, test_inactive_user):
    """Admin lọc người dùng theo trạng thái hoạt động is_active -> 200 OK"""
    response = client.get("/users?status=false", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert any(u["email"] == test_inactive_user.email for u in data["data"])


def test_regular_user_cannot_access_admin_users_list(client, user_headers):
    """User thường truy cập danh sách user của Admin -> 403 Forbidden"""
    response = client.get("/users", headers=user_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["statusCode"] == 403
    assert "Quyền truy cập bị từ chối" in data["message"]
