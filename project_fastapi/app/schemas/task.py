from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

from app.models import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: datetime
    priority: TaskPriority
    
    
class TaskUpdate(BaseModel):
    title: str | None = Field(None, max_length=1000)
    description: str | None = Field(None, max_length=1000)
    assignee_id: int | None = None
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
    
    class Config:
        from_attributes = True
        
class ListTaskData(BaseModel):
    data: List[TaskData]
    meta: dict