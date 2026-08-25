from fastapi import Depends, APIRouter, Request, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.schemas import ApiResponse, TaskCreate, api_response, TaskData, ListTaskData, TaskUpdate
from .projects import project_router
from app.dependencies import verify_project_member, verify_task_member
from app.models import ProjectModel, ProjectMembersModel, TaskPriority, TaskStatus, TaskModel, RoleProject
from app.services import create_task, get_all_task, get_task_by_id, update_task, del_task
from app.core import ForbiddenException, BadRequestException

task_router = APIRouter(prefix="/tasks", tags=["Task"])


@project_router.post(
    "/{project_id}/tasks",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[TaskData],
    summary="Tạo công việc (task) mới trong dự án",
    description="Thành viên dự án tạo task mới với title, description, due_date, priority. Tự động gán assignee mặc định cho người tạo."
)
def create_task_api(
    request: Request,
    task_data: TaskCreate,
    user_data: tuple[ProjectModel, ProjectMembersModel] = Depends(verify_project_member),
    db: Session = Depends(get_db)
):
    project, member = user_data
    
    new_task = {
        "project_id": project.id,
        "title": task_data.title,
        "description": task_data.description,
        "assignee_id": member.user_id,
        "priority": task_data.priority,
        "due_date": task_data.due_date
    }
    
    task = create_task(task_data=new_task, db=db)
    
    return api_response(
        request,
        201,
        "Tạo task thành công",
        task
    )


@project_router.get(
    "/{project_id}/tasks",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ListTaskData],
    summary="Lấy danh sách task trong dự án (Filter, Search, Sort & Phân trang)",
    description="Chỉ thành viên dự án mới được lấy danh sách task. Hỗ trợ lọc theo user_id, status (TODO, IN_PROGRESS, DONE), priority (LOW, MEDIUM, HIGH), tìm kiếm theo title, phân trang (page, size) và sắp xếp (sort_by, sort_order)."
)
def get_all_task_api(
    request: Request, 
    user_id: int | None = Query(None, description="Lọc theo ID người được giao"),
    status: TaskStatus | None = Query(None, description="Lọc theo trạng thái (TODO, IN_PROGRESS, DONE)"),
    priority: TaskPriority | None = Query(None, description="Lọc theo độ ưu tiên (LOW, MEDIUM, HIGH)"),
    title: str | None = Query(None, description="Tìm kiếm theo tiêu đề"),
    page: int = Query(1, ge=1, description="Trang hiện tại (bắt đầu từ 1)"),
    size: int = Query(10, ge=1, le=100, description="Số lượng task trên mỗi trang"),
    sort_by: str = Query("created_at", description="Trường cần sắp xếp (created_at hoặc due_date)"),
    sort_order: str = Query("desc", description="Chiều sắp xếp (asc hoặc desc)"),
    user_data: tuple[ProjectModel, ProjectMembersModel] = Depends(verify_project_member),
    db: Session = Depends(get_db)
):
    project, _ = user_data
    
    list_task = get_all_task(
        project_id=project.id, 
        db=db,
        user_id=user_id,
        status=status,
        priority=priority,
        title=title,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return api_response(
        request,
        200,
        "Lấy danh sách Task thành công",
        list_task
    )


@task_router.get(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[TaskData],
    summary="Xem chi tiết công việc (task)",
    description="Chỉ thành viên thuộc dự án chứa task mới được quyền xem chi tiết. Chặn người ngoài bằng 403 Forbidden."
)
def get_task_api(
    request: Request,
    task_and_user: tuple[TaskModel, ProjectMembersModel] = Depends(verify_task_member)
):
    task, _ = task_and_user
    
    return api_response(
        request,
        200,
        "Chi tiết task",
        task
    )


@task_router.patch(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[TaskData],
    summary="Cập nhật thông tin task",
    description="Chỉ Assignee hoặc Project Owner mới có quyền cập nhật task. Nếu đổi Assignee, người mới bắt buộc phải là thành viên trong dự án."
)
def update_task_api(
    request: Request,
    task_data: TaskUpdate,
    task_and_user: tuple[TaskModel, ProjectMembersModel] = Depends(verify_task_member),
    db: Session = Depends(get_db)
):
    task, member = task_and_user
    if task.assignee_id != member.user_id and member.role != RoleProject.OWNER:
        raise ForbiddenException("Bạn không có quyền chỉnh sửa task này")
    
    check_task = task_data.model_dump(exclude_unset=True)
    new_assignee = check_task.get("assignee_id")
    if new_assignee:
        is_member = db.query(ProjectMembersModel).filter(
            ProjectMembersModel.project_id == task.project_id,
            ProjectMembersModel.user_id == new_assignee
        ).first()
        if not is_member:
            raise BadRequestException("Người dùng này không phải là thành viên của dự án")
    
    task_update = update_task(task, check_task, db)
    
    return api_response(
        request,
        200,
        "Cập nhật thông tin task thành công",
        task_update
    )


@task_router.delete(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse,
    summary="Xóa công việc (task)",
    description="Chỉ Project Owner mới có quyền xóa task. Thành viên thường hoặc Assignee không có quyền xóa."
)
def del_task_api(
    request: Request,
    task_and_user: tuple[TaskModel, ProjectMembersModel] = Depends(verify_task_member),
    db: Session = Depends(get_db)
):
    task, member = task_and_user
    
    if member.role != RoleProject.OWNER:
        raise ForbiddenException("Bạn không có quyền xóa task này")
    
    del_task(task, db)
    
    return api_response(
        request,
        200,
        "Xóa task thành công"
    )
