import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db
from app.models import UserModel, RoleUser, ProjectModel, ProjectMembersModel, RoleProject
from app.core import hash_password, generate_access_token, generate_refresh_token, settings

# Use SQLite in-memory for fast, isolated, deterministic testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    # Clean tables before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_admin(db_session):
    admin = UserModel(
        email="admin@test.com",
        password_hash=hash_password("AdminPass123!"),
        full_name="Admin Test User",
        role=RoleUser.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_user(db_session):
    user = UserModel(
        email="user@test.com",
        password_hash=hash_password("UserPass123!"),
        full_name="Regular Test User",
        role=RoleUser.USER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session):
    user = UserModel(
        email="user2@test.com",
        password_hash=hash_password("UserPass123!"),
        full_name="Second Test User",
        role=RoleUser.USER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_inactive_user(db_session):
    user = UserModel(
        email="inactive@test.com",
        password_hash=hash_password("UserPass123!"),
        full_name="Inactive Test User",
        role=RoleUser.USER,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(test_admin):
    return generate_access_token(test_admin)


@pytest.fixture
def user_token(test_user):
    return generate_access_token(test_user)


@pytest.fixture
def user2_token(test_user2):
    return generate_access_token(test_user2)


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def user2_headers(user2_token):
    return {"Authorization": f"Bearer {user2_token}"}
