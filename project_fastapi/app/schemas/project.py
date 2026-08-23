from pydantic import BaseModel, Field
from .users import UserData
from datetime import datetime
from typing import Optional
from app.models import RoleProject

class ProjectCreate(BaseModel):
    name:str
    description:str | None = None
    

class AddUserProject(BaseModel):
    user_id: int
    role: RoleProject = Field(default=RoleProject.MEMBER)
    

class UpdateProject(BaseModel):
    name: str | None = None
    description: str | None = None

class ProjectData(BaseModel):
    id: int
    name: str
    description: str | None = None
    owner_id: int
    created_at: datetime
    role_user: RoleProject | None = None
    
    class Config:
        from_attributes = True
    

class ProjectMemberData(BaseModel):
    id: int
    user_id: int
    project_id: int
    role: RoleProject
    joined_at: datetime
    