from fastapi import Depends, APIRouter, Request, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas import ApiResponse, api_response, UserData
from app.core import InvalidInputException, NotFoundException
from app.db import get_db
from app.services import query_user_by_admin, query_user_by_id
from app.dependencies import allow_admin_only, get_current_user

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[UserData],
    summary="Lấy thông tin người dùng hiện tại",
    description="Trả về thông tin chi tiết của người dùng đang đăng nhập dựa trên JWT token (không bao gồm password_hash)."
)
def get_me(request: Request, user_data: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = query_user_by_id(int(user_data.get("sub")), db)
    if not user:
        raise NotFoundException("Người dùng không tồn tại")
    return api_response(
        request,
        200,
        message="Lấy thông tin thành công",
        data=user
    )


@user_router.get(
    "",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(allow_admin_only)],
    response_model=ApiResponse[List[UserData]],
    summary="Quản trị viên lấy danh sách người dùng",
    description="Chỉ tài khoản ADMIN mới có quyền truy cập. Hỗ trợ tìm kiếm theo tên, email và lọc theo trạng thái hoạt động (is_active)."
)
def get_user_by_admin(
    request: Request,
    email: str | None = None,
    name: str | None = None,
    status: bool | None = None,
    db: Session = Depends(get_db)
):
    try:
        list_user = query_user_by_admin(db, name, email, status)
    except Exception:
        raise InvalidInputException()
    
    return api_response(
        request,
        200,
        "Danh sách user",
        list_user
    )