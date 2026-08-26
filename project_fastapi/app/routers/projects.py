from fastapi import Depends, APIRouter, Request, Response, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas import ApiResponse, api_response, ProjectCreate, ProjectData, ProjectMemberData, AddUserProject, UpdateProject, ActivityLogData
from app.core import ForbiddenException, NotFoundException, ConflictException, BadRequestException
from app.db import get_db
from app.models import ProjectMembersModel, RoleProject
from app.services import save_project, query_project_join, join_project, update_project, del_project, del_user_project, query_user_by_id, query_all_project_member, log_activity, query_project_activity_logs
from app.dependencies import get_current_user, verify_project_member


project_router = APIRouter(prefix="/project", tags=["Project"])


@project_router.post(
    "",
    response_model=ApiResponse[ProjectData],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo dự án mới",
    description="Người dùng đăng nhập tạo dự án mới và tự động được gán quyền OWNER của dự án."
)
def create_project_api(
    request: Request,
    project_data: ProjectCreate,
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_project = save_project(project_data.model_dump(), int(user_data.get("sub")), db)
    log_activity(
        project_id=new_project.id,
        user_id=int(user_data.get("sub")),
        action="CREATE_PROJECT",
        details={"name": new_project.name, "description": new_project.description},
        db=db
    )
    
    return api_response(
        request,
        201,
        "Khởi tạo dự án thành công",
        new_project
    )


@project_router.get(
    "",
    response_model=ApiResponse[List[ProjectData]],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách dự án của người dùng",
    description="Chỉ trả về các dự án mà người dùng hiện tại tham gia với tư cách OWNER hoặc MEMBER. Hỗ trợ tìm kiếm theo tên dự án."
)
def get_project_api(
    request: Request,
    search: str | None = None,
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    list_project = query_project_join(int(user_data.get("sub")), db, search)
    
    return api_response(
        request,
        200,
        "Lấy danh sách thành công",
        list_project
    )


@project_router.get(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ProjectData],
    summary="Xem chi tiết dự án",
    description="Chỉ thành viên thuộc dự án mới có quyền xem chi tiết. Chặn người ngoài bằng 403 Forbidden."
)
def get_project_detail_api(
    request: Request,
    project_data = Depends(verify_project_member)
):
    project, member = project_data
    
    return api_response(
        request,
        200,
        "Chi tiết dự án",
        ProjectData(
            id=project.id,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            created_at=project.created_at,
            role_user=member.role
        )
    )


@project_router.post(
    "/{project_id}/member",
    response_model=ApiResponse[ProjectMemberData],
    status_code=status.HTTP_201_CREATED,
    summary="Thêm thành viên vào dự án",
    description="Chỉ OWNER mới có quyền thêm thành viên vào dự án."
)
def add_member_project_api(
    request: Request,
    user_data: AddUserProject,
    project_data = Depends(verify_project_member),
    db: Session = Depends(get_db)
):
    project, member = project_data
    
    if member.role != RoleProject.OWNER:
        raise ForbiddenException("Chỉ Owner mới có quyền thêm thành viên")
    
    target_user = query_user_by_id(user_data.user_id, db)
    if not target_user:
        raise NotFoundException("Người dùng không tồn tại")
    
    existing_member = db.query(ProjectMembersModel).filter(
        ProjectMembersModel.project_id == project.id,
        ProjectMembersModel.user_id == user_data.user_id
    ).first()
    
    if existing_member:
        raise ConflictException("Người dùng đã là thành viên của dự án")
    
    new_member = join_project(user_data.user_id, project.id, db, user_data.role)
    log_activity(
        project_id=project.id,
        user_id=member.user_id,
        action="ADD_MEMBER",
        details={
            "target_user_id": user_data.user_id,
            "role": user_data.role.value if hasattr(user_data.role, 'value') else str(user_data.role)
        },
        db=db
    )
    
    return api_response(
        request,
        201,
        "Thêm thành viên thành công",
        new_member
    )


@project_router.patch(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ProjectData],
    response_model_exclude_unset=True,
    summary="Cập nhật thông tin dự án",
    description="Chỉ OWNER mới có quyền chỉnh sửa thông tin dự án"
)
def update_project_api(
    request: Request,
    data_update: UpdateProject,
    project_data = Depends(verify_project_member),
    db: Session = Depends(get_db)
):
    project, member = project_data
    
    if member.role != RoleProject.OWNER:
        raise ForbiddenException("Bạn không có quyền sửa đổi dự án")
    
    update_dict = data_update.model_dump(exclude_unset=True)
    project_new = update_project(update_dict, project, db)
    log_activity(
        project_id=project.id,
        user_id=member.user_id,
        action="UPDATE_PROJECT",
        details=update_dict,
        db=db
    )
    
    return api_response(
        request,
        200,
        "Cập nhật project thành công",
        project_new
    )


@project_router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa dự án",
    description="Chỉ OWNER mới có quyền xóa dự án. Tự động xóa liên hoàn các thành viên và task liên quan."
)
def del_project_api(
    request: Request,
    project_data = Depends(verify_project_member),
    db: Session = Depends(get_db)
):
    project, member = project_data
        
    if member.role != RoleProject.OWNER:
        raise ForbiddenException("Bạn không có quyền xóa dự án")
    
    del_project(project, db)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@project_router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa thành viên khỏi dự án",
    description="Chỉ OWNER mới có quyền xóa thành viên. Không cho phép xóa người khởi tạo dự án (Owner chính)."
)
def del_project_member_api(
    request: Request,
    user_id: int,
    project_data: tuple[ProjectData, ProjectMembersModel] = Depends(verify_project_member),
    db: Session = Depends(get_db)
):
    project, member = project_data
    
    if member.role != RoleProject.OWNER:
        raise ForbiddenException("Bạn không có quyền thực hiện hành động này")
    
    if user_id == project.owner_id:
        raise BadRequestException("Không thể xóa người khởi tạo dự án")
    
    del_user_project(project.id, user_id, db)
    log_activity(
        project_id=project.id,
        user_id=member.user_id,
        action="REMOVE_MEMBER",
        details={"target_user_id": user_id},
        db=db
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@project_router.get(
    "/{project_id}/members",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[List[ProjectMemberData]],
    summary="Lấy danh sách thành viên trong dự án",
    description="Trả về toàn bộ danh sách thành viên kèm role tương ứng trong dự án"
)
def get_all_member_api(
    request: Request,
    project_data = Depends(verify_project_member),
    db: Session = Depends(get_db)
):
    project, _ = project_data
    
    list_member = query_all_project_member(project_id=project.id, db=db)
    
    return api_response(
        request,
        200,
        "Lấy danh sách thành viên thành công",
        list_member
    )
 

@project_router.get(
    "/{project_id}/activities",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[List[ActivityLogData]],
    summary="Lấy lịch sử thao tác của dự án",
    description="Chỉ thành viên thuộc dự án mới có quyền xem lịch sử thao tác"
)
def get_project_activities_api(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    project_data = Depends(verify_project_member),
    db: Session = Depends(get_db)
):
    project, _ = project_data
    
    list_activities = query_project_activity_logs(
        project_id=project.id,
        db=db,
        limit=limit,
        offset=offset
    )
    
    return api_response(
        request,
        200,
        "Lấy lịch sử thao tác thành công",
        list_activities
    )
