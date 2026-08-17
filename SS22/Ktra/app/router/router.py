from fastapi import APIRouter, status, HTTPException, Depends, Request
from app.schemas import *
from app.database import get_db
from sqlalchemy.orm import Session
from app.services import *
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidSignatureError, InvalidKeyError

load_dotenv()
TRUSTBANK_SECRET_KEY = os.getenv("TRUSTBANK_SECRET_KEY")


router = APIRouter(prefix="/api", tags=["Users"])

security  = HTTPBearer()

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
    

@router.get("/account/balance", status_code=status.HTTP_200_OK)
def get_balance(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try: 
        token = jwt.decode(credentials.credentials, TRUSTBANK_SECRET_KEY,"HS256")

    except (InvalidSignatureError, InvalidKeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_TOKEN"
            )
    
    user = query_username(username=token["sub"], db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="USER_NOT_FOUND")
    
    return {
        "statusCode": 200,
        "message": f"Chào mừng {user.username}",
        "balance": user.balance
    }


        
@router.post("/auth/change-password", status_code=status.HTTP_200_OK)
def change_password(password_data: ChangePasswordRequest ,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = jwt.decode(credentials.credentials, TRUSTBANK_SECRET_KEY, "HS256")
    except (InvalidSignatureError, InvalidKeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_TOKEN"
            )
    
    password = password_data.model_dump()
    user = query_username(token["sub"], db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="USER_NOT_FOUND")
    
    
    if password["old_password"] == password["new_password"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BAD_REQUEST"
        )
    
    if not verity_password(password=password["old_password"], hash_pw=user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CREDENTIALS")
    
    setattr(user,"hashed_password", hash_password(password=password["new_password"]))
    db.commit()
    
    return {
        "statusCode": 200,
        "message": "Cập nhật mật khẩu thành công"
    }
    
@router.post("/account/transfer", status_code=status.HTTP_200_OK)
def account_transfer(transfer_data: TransferRequest ,credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = jwt.decode(credentials.credentials, TRUSTBANK_SECRET_KEY, "HS256")
    except (InvalidSignatureError, InvalidKeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_TOKEN"
            )
            
    transfer = transfer_data.model_dump()
    user = query_username(token["sub"], db)
    user_2 = query_username(transfer["to_username"], db)
    
    if user.username == user_2.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_TRANSFER"
        )
    
    if user.balance < transfer["amount"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INSUFFICIENT_BALANCE"
        )
    
    if not user or not user_2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RECIPIENT_NOT_FOUND")
    transaction(user1=user, user2=user_2, amount=transfer["amount"], db=db)
    
    return {
        "statusCode": 200,
        "message": "Giao dịch thành công"
    }
    
@router.get("/admin/users", status_code=status.HTTP_200_OK)
def admin_get_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = jwt.decode(credentials.credentials, TRUSTBANK_SECRET_KEY, "HS256")
    except (InvalidSignatureError, InvalidKeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_TOKEN"
            )
    if token["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PERMISSION_DENIED"
        )
    
    return {
        "message": "Danh sách tất cả user",
        "data": query_all_user(db)
    }
            
    