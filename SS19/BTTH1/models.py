from typing import List, Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    warehouse_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    # Quan hệ 1-N: Một Warehouse chứa nhiều Packages
    packages: Mapped[List["Package"]] = relationship(
        back_populates="warehouse",
        cascade="all, delete-orphan"
    )

class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    package_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    weight: Mapped[float] = mapped_column(nullable=False)
    warehouse_id: Mapped[Optional[int]] = mapped_column(ForeignKey("warehouses.id"))

    warehouse: Mapped[Optional["Warehouse"]] = relationship(back_populates="packages")
    
    waybill: Mapped[Optional["Waybill"]] = relationship(
        back_populates="package",
        uselist=False,
        cascade="all, delete-orphan"
    )

class Waybill(Base):
    __tablename__ = "waybills"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tracking_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    shipping_status: Mapped[str] = mapped_column(String(50), nullable=False)
    package_id: Mapped[Optional[int]] = mapped_column(ForeignKey("packages.id"), unique=True)

    package: Mapped[Optional["Package"]] = relationship(back_populates="waybill")