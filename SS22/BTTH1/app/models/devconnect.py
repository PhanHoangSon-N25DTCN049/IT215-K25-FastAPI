from app.database import Base
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

class UsersModel(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

