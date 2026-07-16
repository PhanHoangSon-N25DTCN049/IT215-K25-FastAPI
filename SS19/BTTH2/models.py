from typing import List, Optional
from sqlalchemy import ForeignKey, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    clinic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(String(255), nullable=False)

    # Quan hệ 1-N: 1 Phòng khám chứa nhiều Bác sĩ
    doctors: Mapped[List["Doctor"]] = relationship(
        back_populates="clinic", 
        cascade="all, delete-orphan"
    )

class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    doctor_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    clinic_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clinics.id"))

    # Quan hệ N-1 thuộc về Clinic
    clinic: Mapped[Optional["Clinic"]] = relationship(back_populates="doctors")
    
    # Quan hệ 1-1 với License (Bắt buộc uselist=False)
    license: Mapped[Optional["License"]] = relationship(
        back_populates="doctor", 
        uselist=False, 
        cascade="all, delete-orphan"
    )

class License(Base):
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    issue_by: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Ràng buộc unique=True cho khóa ngoại để đảm bảo tính 1-1
    doctor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("doctors.id"), unique=True)

    # Quan hệ 1-1 với Doctor
    doctor: Mapped[Optional["Doctor"]] = relationship(back_populates="license")