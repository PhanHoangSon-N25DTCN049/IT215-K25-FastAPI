from ..database import Base
from sqlalchemy import String, Integer, Float, DateTime, func
from datetime import datetime
import enum

from sqlalchemy.orm import Mapped, mapped_column

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

class Users(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable= True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column( default="customer")
    balance: Mapped[float] = mapped_column(Float, default=10000.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    