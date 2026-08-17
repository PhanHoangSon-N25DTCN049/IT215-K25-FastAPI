from fastapi import APIRouter, status, HTTPException, Depends
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.devconnect import *
from app.schemas.auth import *
from datetime import datetime
from app.services.auth import *
import os
import jwt
from dotenv import load_dotenv
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

router = APIRouter(prefix="/api", tags=["Auth"])

@router.post("/register",status_code=status.HTTP_201_CREATED)
def user_register(user_data: Auth ,db: Session = Depends(get_db)):
   
    user = user_data.model_dump()
    
    user_db = db.query(UsersModel).filter(UsersModel.username == user["username"]).first()
    
    if user_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên đăng nhập đã tồn tại")
    
    new_user = UsersModel(
        username = user["username"],
        hashed_password=hash_password(user["password"])
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

            
        
    return {
        "statusCode":201,
        "message": "Tạo tài khoản thành công",
        "data": new_user
    }
        
@router.post("/login", status_code=status.HTTP_200_OK)
def user_login(user_data: Auth ,db: Session = Depends(get_db)):   
    user = user_data.model_dump()
    
    user_db = db.query(UsersModel).filter(UsersModel.username == user["username"]).first()
    
    if not user_db or not verify_password(user["password"], user_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    now = datetime.now()
    payload = {
        "sub": str(user_db.id),
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + (60*30)
    }
    
    token = jwt.encode(payload, SECRET_KEY,algorithm="HS256")

            
    return {
        "statusCode": 200,
        "message": "Đăng nhập thành công",
        "data": token
    }

security = HTTPBearer()

@router.get("/profile", status_code=status.HTTP_200_OK)
def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):

    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        
        user_id = payload.get("sub")
        
       
        user_db = db.query(UsersModel).filter(UsersModel.id == user_id).first()
        
        if not user_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Không tìm thấy người dùng"
            )
            
        
        return {
            "message": f"Welcome, {user_db.username}!"
        }
        
    except ExpiredSignatureError:
        # Lỗi sinh ra khi token đã quá hạn (sau 30 phút)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token đã hết hạn"
        )
    except InvalidTokenError:
        # Lỗi sinh ra khi token sai chữ ký, bị chỉnh sửa hoặc không đúng cấu trúc
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token không hợp lệ"
        )