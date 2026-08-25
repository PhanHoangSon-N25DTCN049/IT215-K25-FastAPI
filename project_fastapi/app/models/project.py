from app.db import Base
from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Enum, UniqueConstraint, BOOLEAN
import enum
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

if TYPE_CHECKING:
    from app.models import UserModel, ProjectMembersModel, TaskModel, ActivityLogModel

class RoleProject(str, enum.Enum):
    OWNER = "owner"
    MEMBER = "member"

class ProjectModel(Base):
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    is_delete: Mapped[bool] = mapped_column(BOOLEAN, default=False)


    
    owner: Mapped["UserModel"] = relationship(back_populates="project")
    project_member: Mapped[List["ProjectMembersModel"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    task: Mapped[List["TaskModel"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    activity_logs: Mapped[List["ActivityLogModel"]] = relationship(back_populates="project")
    
    

class ProjectMembersModel(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    role: Mapped["RoleProject"] = mapped_column(Enum(RoleProject), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    project: Mapped["ProjectModel"] = relationship(back_populates="project_member")
    user: Mapped["UserModel"] = relationship(back_populates="project_member")