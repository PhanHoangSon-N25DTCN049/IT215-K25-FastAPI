from app.db import Base
from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Enum
import enum
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    
class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

if TYPE_CHECKING:
    from app.models import ProjectModel, UserModel

class TaskModel(Base):
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    assignee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    status: Mapped["TaskStatus"] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    priority: Mapped["TaskPriority"] = mapped_column(Enum(TaskPriority), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    
    project: Mapped["ProjectModel"] = relationship(back_populates="task")
    assignee: Mapped["UserModel"] = relationship(back_populates="task")
    comment: Mapped[List["CommentTaskModel"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    
    
class CommentTaskModel(Base):
    __tablename__ = "task_comment"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["UserModel"] = relationship(back_populates="comment")
    task: Mapped["TaskModel"] = relationship(back_populates="comment")
    