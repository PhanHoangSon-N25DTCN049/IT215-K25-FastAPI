from fastapi import APIRouter, Depends, Request, Form, status
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError, InvalidTokenError
from pydantic import EmailStr

from app.db import get_db
from app.core import *
from app.schemas import ApiResponse, UserCreate, api_response, UserData, TokenDataResponse, RefreshRequest
from app.services import query_user_by_gmail, register, save_refresh_token, query_user_by_id
from app.models import RoleUser


auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[UserData],
    summary="Đăng ký tài khoản người dùng mới",
    description="Tạo tài khoản mới với email, password tối thiểu 6 ký tự và họ tên."
)
def register_auth(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    
    if query_user_by_gmail(user_data.email, db):
        raise ConflictException(message="Email đã tồn tại")
    
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


@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[TokenDataResponse],
    summary="Đăng nhập và nhận JWT Access/Refresh Token",
    description="Xác thực thông tin email và mật khẩu qua form-data. Giới hạn tần suất 5 lần / phút."
)
@limiter.limit("5/minute")
def login_auth(request: Request, email: EmailStr = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = query_user_by_gmail(email, db=db)
    check_user = True
    if user:
       if verify_password(password, user.password_hash):
            check_user = False
    if check_user:
        raise UnauthorizedException("Thông tin đăng nhập không đúng")
    
    if not user.is_active:
        raise BadRequestException("Tài khoản của bạn đã bị khóa")
    
    refresh_token = generate_refresh_token(user)
    
    save_refresh_token(user, refresh_token, db)
    
    return api_response(
        request,
        200,
        "Đăng nhập thành công",
        TokenDataResponse(
            access_token=generate_access_token(user),
            refresh_token=refresh_token,
            token_type="bearer"
        )
    )

@auth_router.post(
    "/refresh",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[TokenDataResponse],
    summary="Cấp mới Access Token bằng Refresh Token",
    description="Gửi Refresh Token còn hạn và chưa bị thu hồi để nhận Access Token mới."
)
def refresh_access_token(request: Request, data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.refresh_token, settings.REFRESH_SECRET_KEY, [settings.ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise UnauthorizedException(
                message="Token không hợp lệ (thiếu định danh người dùng)",
                headers={"WWW-Authenticate": "Bearer"}
            )
        user = query_user_by_id(int(sub), db)
        if not user or user.refresh_token != data.refresh_token or user.is_revoked == True:
            raise UnauthorizedException(
                message="Token không còn hợp lệ",
                headers={"WWW-Authenticate": "Bearer"}
                )
        
        return api_response(
            request,
            201,
            "Yêu cầu cấp access token thành công",
            TokenDataResponse(
                access_token=generate_access_token(user),
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
