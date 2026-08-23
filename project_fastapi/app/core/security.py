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


def generate_token(user: "UserModel", time: int, key: str) -> str:
    expire_timestamp = datetime.now().timestamp() + (time * 60)
    return jwt.encode(
            payload={"sub": str(user.id), "exp": expire_timestamp},
            key=key,
            algorithm=settings.ALGORITHM)
    