from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # Ví dụ: "Admin", "Manager", “User”
    description = Column(String(255), nullable=True)
    # Quan hệ Một - Nhiều với bảng User
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Khóa ngoại liên kết tới bảng Role
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    # Thiết lập mối quan hệ để dễ dàng truy cập tên vai trò qua `user.role.name`
    role = relationship("Role", back_populates="users")
