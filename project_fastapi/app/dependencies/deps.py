import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core import ForbiddenException, settings, UnauthorizedException, NotFoundException
from app.db import get_db
from app.models import RoleUser, ProjectMembersModel, ProjectModel, TaskModel
from app.services import get_task_by_id


security = HTTPBearer()


def get_current_user(
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

    
    if not payload.get("sub"):
        raise UnauthorizedException(
            message="Token không hợp lệ (thiếu định danh người dùng)",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    return payload


class RoleChecker:
    """
    Sử dụng cơ chế Parameterized Dependency để kiểm tra quyền truy cập động.
    trả về dict bao gồm id và role
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, current_user: dict = Depends(get_current_user)
    ) -> dict:
        if current_user.get("role") not in self.allowed_roles:
            raise ForbiddenException(message="Quyền truy cập bị từ chối.")
        return current_user


allow_admin_only = RoleChecker([RoleUser.ADMIN])
allow_user_and_admin = RoleChecker([RoleUser.USER, RoleUser.ADMIN])


def verify_project_member(
    project_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
) -> tuple[ProjectModel, ProjectMembersModel]:
    """_summary_

    Args:
        project_id (int): nhận vào project id
        db (Session, optional): tạo phiên làm việc db
        user (dict, optional): lấy thông tin id user hiện tại bao gồm id và role

    Raises:
        NotFoundException: kiểm tra dự án tồn tại
        ForbiddenException: kiểm tra quyền truy cập nếu là member hoặc owner thì cho qua

    Returns:
        tuple[ProjectModel, ProjectMembersModel]: trả về tuple project đang làm việc và thông tin user trong project
    """
    user_id = int(user.get("sub"))
    
    result = db.query(ProjectModel, ProjectMembersModel)\
        .outerjoin(
            ProjectMembersModel, 
            (ProjectMembersModel.project_id == ProjectModel.id) & 
            (ProjectMembersModel.user_id == user_id)
        )\
        .filter(ProjectModel.id == project_id, ProjectModel.is_delete == False)\
        .first()
    
    if not result:
        raise NotFoundException("Dự án không tồn tại")
    
    project, member = result
    
    if not member:
        raise ForbiddenException("Bạn không có quyền truy cập dự án này")
    
    return (project, member)

def verify_task_member(
    task_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
)-> tuple[TaskModel, ProjectMembersModel]:
    """

    Args:
        task_id (int): nhận vào task_id
        db (Session): kích hoạt phiên làm việc database
        user (dict, optional): lấy thông tin id user hiện tại bao gồm id và role

    Raises:
        NotFoundException: khi không tồn tại ta
        ForbiddenException: khi không phải là thành viên dự án

    Returns:
        tuple[TaskModel, ProjectMembersModel]: trả về tuple task đang làm việc và thông tin user trong project
    """
    user_id = int(user.get("sub"))
    
    result = db.query(TaskModel, ProjectMembersModel)\
        .join(ProjectModel, ProjectModel.id == TaskModel.project_id)\
        .outerjoin(
            ProjectMembersModel,
            (ProjectMembersModel.project_id == TaskModel.project_id) & 
            (ProjectMembersModel.user_id == user_id)
        )\
        .filter(TaskModel.id == task_id, ProjectModel.is_delete == False)\
        .first()

        
    if not result:
        raise NotFoundException("Task không tồn tại")
        
    task, member = result
    
    if not member:
        raise ForbiddenException("Bạn không có quyền truy cập vào task này")
        
    return (task, member)