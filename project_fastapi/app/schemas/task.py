from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List

from app.models import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    due_date: datetime | None = None
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    
    
class CreateComment(BaseModel):
    content: str
    
    
class CommentData(BaseModel):
    id: int
    task_id: int
    user_id: int
    content: str
    created_at: datetime
    
class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    assignee_id: int | None = Field(None, ge=1)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    
class TaskData(BaseModel):
    id: int
    project_id: int 
    title: str
    description: str | None = None
    assignee_id: int | None = None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
        
class ListTaskData(BaseModel):
    data: List[TaskData]
    meta: dict
