from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

ALLOWED_ORIGIN = "https://internal.megamart.com"
EVIL_ORIGIN = "https://evil-attacker.xyz"


def test_cors_policy():
    print("\n--- KIEM THU CAU HINH CORS ---")

    # 1. Domain hop le tu MegaMart
    res = client.get("/health", headers={"Origin": ALLOWED_ORIGIN})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
    print(f"[PASS] CORS cho phep domain hop le: {ALLOWED_ORIGIN}")

    # 2. Domain gia mao cua hacker
    res = client.get("/health", headers={"Origin": EVIL_ORIGIN})
    assert res.headers.get("access-control-allow-origin") is None
    print(f"[PASS] CORS chan dung domain gia mao: {EVIL_ORIGIN}")


def test_rbac_salary_modify():
    print("\n--- KIEM THU ENDPOINT: GET /api/v1/salary/modify (ADMIN & HR) ---")

    # ADMIN: Allowed
    res = client.get("/api/v1/salary/modify", headers={"X-User-Role": "ADMIN"})
    assert res.status_code == 200
    assert "ADMIN" in res.json().get("requested_by", "")
    print("[PASS] ADMIN truy cap /salary/modify -> 200 OK")

    # HR: Allowed
    res = client.get("/api/v1/salary/modify", headers={"X-User-Role": "HR"})
    assert res.status_code == 200
    assert "HR" in res.json().get("requested_by", "")
    print("[PASS] HR truy cap /salary/modify -> 200 OK")

    # STAFF: Forbidden
    res = client.get("/api/v1/salary/modify", headers={"X-User-Role": "STAFF"})
    assert res.status_code == 403
    assert res.json() == {"error": "Permission Denied"}
    print("[PASS] STAFF bi chan tai /salary/modify -> 403 Forbidden {'error': 'Permission Denied'}")

    # No Header: Forbidden
    res = client.get("/api/v1/salary/modify")
    assert res.status_code == 403
    assert res.json() == {"error": "Permission Denied"}
    print("[PASS] Khong co Header bi chan tai /salary/modify -> 403 Forbidden")


def test_rbac_system_settings():
    print("\n--- KIEM THU ENDPOINT: GET /api/v1/system/settings (CHI ADMIN) ---")

    # ADMIN: Allowed
    res = client.get("/api/v1/system/settings", headers={"X-User-Role": "ADMIN"})
    assert res.status_code == 200
    print("[PASS] ADMIN truy cap /system/settings -> 200 OK")

    # HR: Forbidden
    res = client.get("/api/v1/system/settings", headers={"X-User-Role": "HR"})
    assert res.status_code == 403
    assert res.json() == {"error": "Permission Denied"}
    print("[PASS] HR bi chan tai /system/settings -> 403 Forbidden")

    # STAFF: Forbidden
    res = client.get("/api/v1/system/settings", headers={"X-User-Role": "STAFF"})
    assert res.status_code == 403
    assert res.json() == {"error": "Permission Denied"}
    print("[PASS] STAFF bi chan tai /system/settings -> 403 Forbidden")


def test_rbac_profile():
    print("\n--- KIEM THU ENDPOINT: GET /api/v1/profile (ADMIN, HR, STAFF) ---")

    for role in ["ADMIN", "HR", "STAFF"]:
        res = client.get("/api/v1/profile", headers={"X-User-Role": role})
        assert res.status_code == 200
        print(f"[PASS] {role} truy cap /profile -> 200 OK")

    # Invalid Role: Forbidden
    res = client.get("/api/v1/profile", headers={"X-User-Role": "GUEST"})
    assert res.status_code == 403
    assert res.json() == {"error": "Permission Denied"}
    print("[PASS] Role bat hop le (GUEST) bi chan -> 403 Forbidden")


if __name__ == "__main__":
    test_cors_policy()
    test_rbac_salary_modify()
    test_rbac_system_settings()
    test_rbac_profile()
    print("\n=======================================================")
    print("[SUCCESS] TAT CA CAC BAI KIEM THU SECURITY DA VUOT QUA!")
    print("=======================================================")
