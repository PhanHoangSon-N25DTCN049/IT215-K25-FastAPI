from datetime import datetime
from typing import TYPE_CHECKING
import bcrypt
import jwt
from .config import settings

if TYPE_CHECKING:
    from app.models import UserModel


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt()).decode()


def verify_password(password: str, hash_pw: str) -> bool:
    return bcrypt.checkpw(password=password.encode(), hashed_password=hash_pw.encode())


def generate_access_token(user: "UserModel") -> str:
    expire_timestamp = datetime.now().timestamp() + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    return jwt.encode(
            payload={"sub": str(user.id), "role": role_value,"exp": expire_timestamp},
            key=settings.SECRET_KEY,
            algorithm=settings.ALGORITHM)
    
def generate_refresh_token(user: "UserModel") -> str:
    expire_timestamp = datetime.now().timestamp() + (settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60)
    return jwt.encode(
                payload={"sub": str(user.id), "exp": expire_timestamp},
                key=settings.REFRESH_SECRET_KEY,
                algorithm=settings.ALGORITHM)