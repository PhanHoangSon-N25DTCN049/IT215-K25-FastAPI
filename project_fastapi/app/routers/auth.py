from fastapi import APIRouter, HTTPException, status, Depends, Request, Form
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError, InvalidTokenError

from app.db import get_db
from app.core import *
from app.schemas import ApiResponse, UserCreate, api_response, UserData, TokenDataResponse, RefreshRequest
from app.services import query_user_by_gmail, register, validate_password, save_refresh_token, query_user_by_id
from app.models import RoleUser




auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/register", status_code=201, response_model=ApiResponse[UserData])
def register_auth(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    
    if query_user_by_gmail(user_data.email, db):
        raise ConflictException(message="Email đã tồn tại")
    
    if not validate_password(user_data.password):
        raise InvalidInputException()
    
    new_user = {
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "full_name": user_data.full_name,
        # "role": RoleUser.ADMIN
    }
    
    try:
        user = register(user_data=new_user, db=db)
    except Exception:
        db.rollback()
        raise ConflictException()
    
    return api_response(
        request,
        201,
        "Tạo tài khoản thành công",
        user
    )


@auth_router.post("/login", status_code=200, response_model=ApiResponse[TokenDataResponse])
def login_auth( request: Request,email = Form(), password = Form(min_length=6), db: Session = Depends(get_db)):
    user = query_user_by_gmail(email, db=db)
    check_user = True
    if user:
       if verify_password(password, user.password_hash):
            check_user = False
    if check_user:
        raise UnauthorizedException("Thông tin đăng nhập không đúng")
    
    if not user.is_active:
        raise ForbiddenException("Tài khoản của bạn đã bị khóa")
    
    refresh_token = generate_token(user, settings.REFRESH_TOKEN_EXPIRE_MINUTES, settings.REFRESH_SECRET_KEY)
    
    save_refresh_token(user, refresh_token, db)
    
    return api_response(
        request,
        200,
        "Đăng nhập thành công",
        TokenDataResponse(
            access_token=generate_token(user, settings.ACCESS_TOKEN_EXPIRE_MINUTES, settings.SECRET_KEY),
            refresh_token=refresh_token,
            token_type="bearer"
        )
    )

@auth_router.post("/refresh", status_code=201, response_model=ApiResponse[TokenDataResponse])
def refresh_access_token(request: Request, data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.refresh_token, settings.REFRESH_SECRET_KEY, [settings.ALGORITHM])
        user = query_user_by_id(payload.get("sub"), db)
        if user.refresh_token != data.refresh_token or user.is_revoked == True:
            raise UnauthorizedException(
                message="Token không còn hợp lệ",
                headers={"WWW-Authenticate": "Bearer"}
                )
        
        return api_response(
            request,
            201,
            "Yêu cầu cấp access token thành công",
            TokenDataResponse(
                access_token=generate_token(user, settings.ACCESS_TOKEN_EXPIRE_MINUTES, settings.SECRET_KEY),
                refresh_token= data.refresh_token,
                token_type="bearer"
            )
        )
        
    except ExpiredSignatureError:
        raise UnauthorizedException(
            message="Token đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"}
            )
    except (InvalidTokenError, PyJWTError):
            raise UnauthorizedException(
                message="Không thể xác thực thông tin",
                headers={"WWW-Authenticate": "Bearer"},
            )
        

