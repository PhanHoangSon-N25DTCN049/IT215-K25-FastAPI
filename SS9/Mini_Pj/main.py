from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, Tuple
from datetime import datetime, timezone

app = FastAPI()

# 1. Khởi tạo dữ liệu mô phỏng (In-memory Database)
tasks_db = [
    {
        "id": 1, 
        "title": "Thiet ke database Shop AI", 
        "description": "Xay dung bang va toi uu index", 
        "assignee": "QuyDev", 
        "priority": 1, 
        "status": "todo",
        "created_at": "2026-07-01T09:00:00Z"
    },
    {
        "id": 2, 
        "title": "Code bo API Authen", 
        "description": "Trien khai filter verify JWT token", 
        "assignee": "FixerQ", 
        "priority": 2, 
        "status": "done",
        "created_at": "2026-07-01T10:00:00Z"
    }
]

# 2. Hàm hỗ trợ đóng gói Response 6 trường bắt buộc (Unified Envelope)
def build_response(status_code: int, message: str, data: Any, error: Optional[str], path: str) -> dict:
    return {
        "statusCode": status_code,
        "message": message,
        "data": data,
        "error": error,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "path": path
    }

# Khai báo Custom Exception để xử lý lỗi nghiệp vụ
class TaskException(Exception):
    def __init__(self, status_code: int, message: str, error_code: str):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code

# 3. Global Exception Handlers (Bẫy lỗi tập trung)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Tránh lộ Stack Trace thô khi có lỗi Runtime hệ thống (Security)
    return JSONResponse(
        status_code=500,
        content=build_response(
            500, 
            "Lỗi hệ thống nội bộ!", 
            None, 
            "ERR-SYS-500: Internal Server Error.", 
            request.url.path
        )
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=build_response(
            422, 
            "Lỗi: Dữ liệu đầu vào không hợp lệ hoặc sai định dạng quy định!", 
            None, 
            "ERR-VAL-422: Validation error at Request Body fields constraint layout.", 
            request.url.path
        )
    )

@app.exception_handler(TaskException)
async def task_exception_handler(request: Request, exc: TaskException):
    return JSONResponse(
        status_code=exc.status_code,
        content=build_response(
            exc.status_code, 
            exc.message, 
            None, 
            exc.error_code, 
            request.url.path
        )
    )

class TaskCreateSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=1)
    assignee: str = Field(..., min_length=1)
    priority: int = Field(..., ge=1, le=5)

    @field_validator('assignee')
    @classmethod
    def validate_assignee(cls, v):
        if not v.strip():
            raise ValueError("assignee không được để trống hoặc chỉ chứa khoảng trắng")
        return v.strip()
        
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError("description không được để trống")
        return v.strip()

class TaskStatusUpdateSchema(BaseModel):
    status: str = Field(..., min_length=1)



@app.get("/tasks")
def get_all_tasks(request: Request, status: Optional[str] = None):
    result = tasks_db
    if status:
        result = [t for t in tasks_db if t["status"] == status]
        
    return JSONResponse(
        status_code=200,
        content=build_response(200, "Lấy danh sách công việc thành công!", result, None, request.url.path)
    )

@app.post("/tasks")
def create_task(task_in: TaskCreateSchema, request: Request):
    if any(t["title"] == task_in.title for t in tasks_db):
        raise TaskException(
            status_code=400,
            message="Lỗi: Tiêu đề công việc này đã tồn tại trong nhóm!",
            error_code="ERR-TASK-01: Task conflict: Title field duplicates an existing record."
        )
    
    new_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": new_id,
        "title": task_in.title,
        "description": task_in.description,
        "assignee": task_in.assignee,
        "priority": task_in.priority,
        "status": "todo",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    tasks_db.append(new_task)
    
    return JSONResponse(
        status_code=201,
        content=build_response(201, "Khởi tạo công việc mới thành công!", new_task, None, request.url.path)
    )

# Chức năng 3: Cập nhật trạng thái tiến độ công việc
@app.put("/tasks/{task_id}")
def update_task_status(task_id: int, status_in: TaskStatusUpdateSchema, request: Request):
    task = next((t for t in tasks_db if t["id"] == task_id), None)
    if not task:
        raise TaskException(
            status_code=404,
            message="Lỗi: Không tìm thấy công việc!",
            error_code="ERR-TASK-03: Task not found."
        )
    
    if task["status"] == "done":
        raise TaskException(
            status_code=400,
            message="Lỗi: Không cho phép cập nhật lùi trạng thái khi đã hoàn thành!",
            error_code="ERR-TASK-04: Cannot update status of a completed task."
        )
        
    task["status"] = status_in.status
    
    return JSONResponse(
        status_code=200,
        content=build_response(200, "Cập nhật tiến độ công việc thành công!", task, None, request.url.path)
    )

def calculate_team_metrics() -> Tuple[int, int, float]:
    total_tasks = len(tasks_db)
    if total_tasks == 0:
        return (0, 0, 0.0)
        
    completed_tasks = sum(1 for t in tasks_db if t["status"] == "done")
    completion_rate = (completed_tasks / total_tasks) * 100
    
    return (total_tasks, completed_tasks, float(completion_rate))

@app.get("/tasks/analytics/dashboard")
def get_dashboard_analytics(request: Request):
    total, completed, rate = calculate_team_metrics()
    
    data = {
        "total_tasks": total,
        "completed_tasks": completed,
        "completion_rate_percentage": round(rate, 1)
    }
    
    return JSONResponse(
        status_code=200,
        content=build_response(200, "Lấy số liệu thống kê hiệu suất nhóm thành công!", data, None, request.url.path)
    )