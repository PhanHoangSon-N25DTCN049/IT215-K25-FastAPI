from app.db import Base
from sqlalchemy import String, Integer, Enum, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from typing import List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models import ProjectModel, ProjectMembersModel, TaskModel

class RoleUser(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class UserModel(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleUser] = mapped_column(Enum(RoleUser),default=RoleUser.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    refresh_token: Mapped[str] = mapped_column(String(1000), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    project: Mapped[List["ProjectModel"]] = relationship(back_populates="owner")
    project_member: Mapped[List["ProjectMembersModel"]] = relationship(back_populates="user")
    task: Mapped[List["TaskModel"]] = relationship(back_populates="assignee")
