import pytest
from datetime import datetime
import jwt
from app.core import settings, generate_refresh_token
from app.services import query_user_by_gmail, save_refresh_token

def test_register_success(client, db_session):
    """Đăng ký tài khoản mới thành công (201 Created)"""
    payload = {
        "email": "newuser@test.com",
        "password": "Password123!",
        "full_name": "New Tester"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["statusCode"] == 201
    assert data["message"] == "Tạo tài khoản thành công"
    assert data["data"]["email"] == "newuser@test.com"
    assert data["data"]["full_name"] == "New Tester"
    assert data["data"]["role"] == "user"
    assert data["data"]["is_active"] is True
    assert "password" not in data["data"]

    # Verify user exists in database
    user = query_user_by_gmail("newuser@test.com", db_session)
    assert user is not None
    assert user.full_name == "New Tester"


def test_register_duplicate_email(client, test_user):
    """Đăng ký với email đã tồn tại -> 409 Conflict"""
    payload = {
        "email": test_user.email,
        "password": "Password123!",
        "full_name": "Duplicate User"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["statusCode"] == 409
    assert "Email đã tồn tại" in data["message"]


def test_register_invalid_email(client):
    """Đăng ký với email không đúng định dạng -> 422 Unprocessable Entity"""
    payload = {
        "email": "not-an-email",
        "password": "Password123!",
        "full_name": "Invalid Email"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["statusCode"] == 422


def test_register_short_password(client):
    """Đăng ký với mật khẩu ngắn hơn 6 ký tự -> 422 Unprocessable Entity"""
    payload = {
        "email": "shortpass@test.com",
        "password": "123",
        "full_name": "Short Password"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["statusCode"] == 422


def test_register_missing_fields(client):
    """Đăng ký thiếu trường bắt buộc -> 422 Unprocessable Entity"""
    response = client.post("/auth/register", json={"email": "missing@test.com"})
    assert response.status_code == 422


def test_login_success(client, test_user):
    """Đăng nhập đúng thông tin -> 200 OK, trả về tokens"""
    response = client.post(
        "/auth/login",
        data={"email": test_user.email, "password": "UserPass123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["statusCode"] == 200
    assert data["message"] == "Đăng nhập thành công"
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    """Đăng nhập sai mật khẩu -> 401 Unauthorized"""
    response = client.post(
        "/auth/login",
        data={"email": test_user.email, "password": "WrongPassword123"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["statusCode"] == 401
    assert "Thông tin đăng nhập không đúng" in data["message"]


def test_login_nonexistent_user(client):
    """Đăng nhập với email không tồn tại -> 401 Unauthorized"""
    response = client.post(
        "/auth/login",
        data={"email": "notfound@test.com", "password": "AnyPassword123"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["statusCode"] == 401
    assert "Thông tin đăng nhập không đúng" in data["message"]


def test_login_inactive_user(client, test_inactive_user):
    """Đăng nhập với tài khoản bị khóa -> 400 Bad Request"""
    response = client.post(
        "/auth/login",
        data={"email": test_inactive_user.email, "password": "UserPass123!"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["statusCode"] == 400
    assert "Tài khoản của bạn đã bị khóa" in data["message"]


def test_login_missing_form_fields(client):
    """Đăng nhập thiếu form field -> 422 Unprocessable Entity"""
    response = client.post("/auth/login", data={"email": "user@test.com"})
    assert response.status_code == 422


def test_refresh_token_success(client, test_user, db_session):
    """Lấy Access Token mới bằng Refresh Token hợp lệ -> 201 Created"""
    refresh_token = generate_refresh_token(test_user)
    save_refresh_token(test_user, refresh_token, db_session)

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 201
    data = response.json()
    assert data["statusCode"] == 201
    assert "access_token" in data["data"]
    assert data["data"]["refresh_token"] == refresh_token
    assert data["data"]["token_type"] == "bearer"


def test_refresh_token_revoked(client, test_user, db_session):
    """Refresh token đã bị thu hồi (is_revoked=True) -> 401 Unauthorized"""
    refresh_token = generate_refresh_token(test_user)
    save_refresh_token(test_user, refresh_token, db_session)
    test_user.is_revoked = True
    db_session.commit()

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401
    data = response.json()
    assert data["statusCode"] == 401
    assert "Token không còn hợp lệ" in data["message"]


def test_refresh_token_mismatched(client, test_user, db_session):
    """Refresh token hợp lệ về mặt chữ ký nhưng không khớp với token lưu trong DB -> 401 Unauthorized"""
    old_token = generate_refresh_token(test_user)
    save_refresh_token(test_user, old_token, db_session)

    new_token = generate_refresh_token(test_user)
    response = client.post("/auth/refresh", json={"refresh_token": new_token})
    assert response.status_code == 401
    data = response.json()
    assert data["statusCode"] == 401
    assert "Token không còn hợp lệ" in data["message"]


def test_refresh_token_expired(client, test_user):
    """Refresh token đã hết hạn -> 401 Unauthorized"""
    expired_payload = {
        "sub": str(test_user.id),
        "exp": datetime.now().timestamp() - 3600  # 1 hour in the past
    }
    expired_token = jwt.encode(expired_payload, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)

    response = client.post("/auth/refresh", json={"refresh_token": expired_token})
    assert response.status_code == 401
    data = response.json()
    assert data["statusCode"] == 401
    assert "Token đã hết hạn" in data["message"]


def test_refresh_token_invalid_signature(client):
    """Refresh token sai secret key -> 401 Unauthorized"""
    invalid_token = jwt.encode(
        {"sub": "1", "exp": datetime.now().timestamp() + 3600},
        "wrong_secret_key",
        algorithm="HS256"
    )
    response = client.post("/auth/refresh", json={"refresh_token": invalid_token})
    assert response.status_code == 401
    data = response.json()
    assert data["statusCode"] == 401
    assert "Không thể xác thực thông tin" in data["message"]


def test_login_rate_limit_exceeded(client, test_user):
    """Gọi đăng nhập vượt quá 5 lần / phút -> 429 Too Many Requests"""
    # 5 requests within limit (regardless of success/failure)
    for _ in range(5):
        client.post("/auth/login", data={"email": "wrong@test.com", "password": "wrongpassword"})
    
    # 6th request must trigger rate limit
    response = client.post("/auth/login", data={"email": test_user.email, "password": "Password123!"})
    assert response.status_code == 429
    data = response.json()
    assert data["statusCode"] == 429
    assert "Bạn đã thử quá số lần cho phép" in data["message"]

