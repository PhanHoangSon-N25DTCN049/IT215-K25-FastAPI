from app.database import Base
from sqlalchemy import Integer, String,ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List
class DepartmentsModel(Base):
    __tablename__ = "departments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) 
    department_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=True)
    department_name: Mapped[str] = mapped_column(String(255), nullable=True)
    
    employees: Mapped[List["Employees"]] = relationship(back_populates="department")
    
class Employees(Base):
    __tablename__ = "employees"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) 
    employee_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    department: Mapped["DepartmentsModel"] = relationship(back_populates="employees")
    