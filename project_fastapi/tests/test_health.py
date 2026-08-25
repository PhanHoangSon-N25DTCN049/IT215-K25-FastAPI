import pytest

def test_health_check_success(client):
    """Kiểm tra endpoint GET / kết nối database thành công"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data.get("message") == "Kết nối database Thành công"
