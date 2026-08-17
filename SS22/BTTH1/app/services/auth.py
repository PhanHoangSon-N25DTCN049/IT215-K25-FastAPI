import jwt
import bcrypt

def hash_password(password: str) -> str:
    hash_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hash_pw.decode()

def verify_password(password: str, hash_password: str) -> bool:
    return bcrypt.checkpw(password=password.encode(), hashed_password=hash_password.encode())
