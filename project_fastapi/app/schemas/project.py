from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models import RoleProject

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    

class AddUserProject(BaseModel):
    user_id: int
    role: RoleProject = Field(default=RoleProject.MEMBER)
    
class ProjectMemberData(BaseModel):
    id: int | None = None
    user_id: int
    project_id: int | None = None
    role: RoleProject
    joined_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class UpdateProject(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)

class ProjectData(BaseModel):
    id: int
    name: str
    description: str | None = None
    owner_id: int    
    created_at: datetime
    role_user: RoleProject | None = None
    
    model_config = ConfigDict(from_attributes=True)

    