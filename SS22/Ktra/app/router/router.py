from fastapi import APIRouter, status, HTTPException, Depends, Request
from app.schemas import *
from app.database import get_db
from sqlalchemy.orm import Session
from app.services import *
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
TRUSTBANK_SECRET_KEY = os.getenv("TRUSTBANK_SECRET_KEY")


router = APIRouter(prefix="/api", tags=["Users"])



@router.post("/auth/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def register_user(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    user = user_data.model_dump()
    
    if query_username(username=user["username"], db=db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="USER_ALREADY_EXISTS"
        )
    
    new_user = {
        "username": user["username"],
        "hashed_password": hash_password(password=user["password"]),
        "role": user["role"]
    }
    
    new_user = add_user(user_data=new_user, db=db)
    return new_user

@router.post("/auth/login", status_code=status.HTTP_200_OK)
def user_login(user_data:UserLoginRequest ,db: Session = Depends(get_db)):
    user = user_data.model_dump()
    user_db = query_username(username=user["username"], db=db)
    check_user = True
    if user_db:
        if verity_password(password=user["password"], hash_pw=user_db.hashed_password):
            check_user = False
    
    if check_user:        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu"
        )
    
    now = datetime.now().timestamp()
    
    Payload = {
        "sub": user_db.username,
        "role": user_db.role,
        "iat": now,
        "exp": now + (600)
    }
    
    token =  jwt.encode(payload=Payload, key=TRUSTBANK_SECRET_KEY, algorithm="HS256")
    
    return {
        "statusCode": 200,
        "token": token  
    }
    
        