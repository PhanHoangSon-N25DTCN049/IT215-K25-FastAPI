from fastapi import  Depends, APIRouter, Request
from sqlalchemy.orm import Session
from typing import List


from app.schemas import ApiResponse, api_response, ProjectCreate, ProjectData, ProjectMemberData, AddUserProject, UpdateProject
from app.core import ForbiddenException, NotFoundException, ConflictException,BadRequestException
from app.db import get_db
from app.models import  ProjectMembersModel, RoleProject
from app.services import save_project, query_project_join, join_project, update_project, del_project, del_user_project,query_user_by_id
from app.dependencies import get_current_user, verify_project_member


project_router = APIRouter(prefix="/project", tags=["Project"])

@project_router.post("", response_model=ApiResponse[ProjectData], status_code=201)
def create_project_api(request: Request,
                       project_data: ProjectCreate,
                       user_data: dict = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    
    new_project = save_project(project_data.model_dump(), user_data.get("sub"), db)
    
    return api_response(
        request,
        201,
        "Khởi tạo dự án thành công",
        new_project
    )

@project_router.get("", response_model=ApiResponse[List[ProjectData]], status_code=200)
def get_project_api(request: Request,
                    search: str | None = None,
                    user_data: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)
                    ):
    list_project = query_project_join(user_data.get("sub"), db, search)
    
    return api_response(
        request,
        200,
        "Lấy danh sách thành công",
        list_project
    )
    
@project_router.get("/{project_id}", status_code=200, response_model=ApiResponse[ProjectData])
def get_project_detail_api(request: Request, project_data = Depends(verify_project_member)):
    
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
    
@project_router.post("/{project_id}/member", response_model=ApiResponse[ProjectMemberData], status_code=201)
def add_member_project_api(request: Request,
                           user_data: AddUserProject,
                           project_data = Depends(verify_project_member),
                           db: Session = Depends(get_db)):
    
    project, member = project_data
    
    if member.role != RoleProject.OWNER:
        raise ForbiddenException()
    
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
    
    return api_response(
        request,
        201,
        "Thêm thành viên thành công",
        new_member
    )
    
@project_router.patch("/{project_id}", status_code=200, response_model=ApiResponse[ProjectData], response_model_exclude_unset=True)
def update_project_api(request: Request,
                       data_update: UpdateProject,
                       project_data = Depends(verify_project_member),
                       db: Session =Depends(get_db)):
    
    project, member = project_data
    
    if member.role != RoleProject.OWNER:
            raise ForbiddenException("Bạn không có quyền sửa đổi dự án")
    
    project_new = update_project(data_update.model_dump(exclude_unset=True), project, db)
    
    return api_response(
        request,
        200,
        "Cập nhật project thành công",
        project_new
    )


@project_router.delete("/{project_id}", status_code=200, response_model=ApiResponse)
def del_project_api(request: Request, project_data = Depends(verify_project_member), db: Session = Depends(get_db)):
    project, member = project_data
        
    if member.role != RoleProject.OWNER:
            raise ForbiddenException("Bạn không có quyền xóa dự án")
    
    del_project(project, db)
    
    return api_response(
        request,
        200,
        "Xóa dự án thành công"
    )

@project_router.delete("/{project_id}/members/{user_id}",status_code=200, response_model=ApiResponse)
def del_project_member_api(request: Request, user_id: int, project_data = Depends(verify_project_member), db:Session = Depends(get_db)):
    project, member = project_data
    
    if member.role != RoleProject.OWNER:
        raise ForbiddenException("Bạn không có quyền thực hiện hành động này")
    
    if user_id == member.user_id: raise BadRequestException("Owner không thể tự xóa chính mình khỏi dự án")
    
    del_user_project(project.id ,user_id, db)
    
    return api_response(
        request,
        200,
        "Xóa thành viên thành công",
    )
    
    
    