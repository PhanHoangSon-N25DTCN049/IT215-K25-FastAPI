import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError
from sqlalchemy.orm import Session

from app.core import ForbiddenException, settings, UnauthorizedException, NotFoundException
from app.db import get_db
from app.models import RoleUser, UserModel, ProjectMembersModel, ProjectModel
from app.services import query_user_by_id

security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise UnauthorizedException(
            message="Token đã hết hạn", headers={"WWW-Authenticate": "Bearer"}
        )
    except (InvalidTokenError, PyJWTError):
        raise UnauthorizedException(
            message="Không thể xác thực thông tin",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = query_user_by_id(payload.get("sub"), db)
    if not user:
        return None

    return user


class RoleChecker:
    """
    Sử dụng cơ chế Parameterized Dependency để kiểm tra quyền truy cập động.
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, current_user: UserModel = Depends(get_current_user)
    ) -> UserModel:
        if current_user.role not in self.allowed_roles:
            raise ForbiddenException(message="Quyền truy cập bị từ chối.")
        return current_user


allow_admin_only = RoleChecker([RoleUser.ADMIN])
allow_user_and_admin = RoleChecker([RoleUser.USER, RoleUser.ADMIN])


def verify_project_member(
    project_id: int,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user)
):
    """_summary_

    Args:
        project_id (int): Nhận vào ID dự án
        user: dựa vào token để lấy user đang thực hiện hàm qua get_current_user


    Returns:
        trả về project và user đang thực hiện hàm
    """
    
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    
    if not project:
        raise NotFoundException("Dự án không tồn tại")
    
    member = db.query(ProjectMembersModel).filter(
        ProjectMembersModel.project_id == project_id,
        ProjectMembersModel.user_id == user.id
    ).first()
    
    if not member:
        raise ForbiddenException("Bạn không có quyền truy cập dự án này")
    
    return (project, member)