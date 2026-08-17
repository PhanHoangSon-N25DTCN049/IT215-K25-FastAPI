from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
MEDCARE_SECRET_KEY = os.getenv("MEDCARE_SECRET_KEY", "fallback_secret_key")
ALGORITHM = "HS256"

app = FastAPI(title="MedCare E-Prescription API")
security = HTTPBearer()

db_users = {}

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str

class LoginRequest(BaseModel):
    username: str
    password: str

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, MEDCARE_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token đã hết hạn. Vui lòng đăng nhập lại."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token không hợp lệ hoặc sai chữ ký."
        )

@app.post("/api/v1/medical/register")
def register(user: RegisterRequest):
    if user.role not in ["doctor", "pharmacist"]:
        raise HTTPException(status_code=400, detail="Role chỉ hợp lệ với giá trị 'doctor' hoặc 'pharmacist'.")
    
    if user.username in db_users:
        raise HTTPException(status_code=400, detail="Username đã tồn tại.")

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), salt)

    db_users[user.username] = {
        "username": user.username,
        "password": hashed_password,
        "role": user.role
    }
    
    return {"message": "Đăng ký tài khoản y tế thành công."}

@app.post("/api/v1/medical/login")
def login(user: LoginRequest):
    db_user = db_users.get(user.username)
    
    error_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Thông tin đăng nhập không chính xác."
    )

    if not db_user:
        raise error_exception

    if not bcrypt.checkpw(user.password.encode('utf-8'), db_user["password"]):
        raise error_exception

    expiration = datetime.utcnow() + timedelta(minutes=20)
    payload = {
        "sub": db_user["username"],
        "role": db_user["role"],
        "iat": datetime.utcnow(),
        "exp": expiration
    }

    token = jwt.encode(payload, MEDCARE_SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": 20
    }

@app.post("/api/v1/prescriptions")
def create_prescription(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bạn không đủ quyền hạn. Chỉ bác sĩ mới được phép tạo đơn thuốc."
        )
    
    return {
        "message": "Đơn thuốc đã được tạo và ký điện tử thành công.",
        "doctor_username": current_user.get("sub")
    }

@app.get("/api/v1/prescriptions/view")
def view_prescriptions(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Truy xuất danh sách đơn thuốc thành công.",
        "viewer_role": current_user.get("role"),
        "viewer_username": current_user.get("sub"),
        "data": [
            {"id": "RX-001", "patient": "Nguyen Van A", "medicine": "Paracetamol 500mg"}
        ]
    }