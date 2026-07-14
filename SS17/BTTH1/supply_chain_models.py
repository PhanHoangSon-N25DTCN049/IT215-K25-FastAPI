from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey, FLOAT, Table, Column


class Base(DeclarativeBase):
    pass


package_truck = Table(
    "package_truck",
    Base.metadata,
    Column("package_id", ForeignKey("package.id"), primary_key=True),
    Column("truck_id", ForeignKey("truck.id"), primary_key=True),
)


class Warehouse(Base):
    __tablename__ = "warehouse"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warehouse_name: Mapped[str] = mapped_column(String(255), nullable= False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    packages: Mapped[list["Package"]] = relationship(back_populates="warehouse")
    
class Package(Base):
    __tablename__ = "package"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    weight: Mapped[float] = mapped_column(FLOAT, nullable=False)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouse.id")) 
    
    warehouse: Mapped["Warehouse"] = relationship(back_populates="packages")
    waybill: Mapped["Waybill"] = relationship(back_populates="package", uselist=False)
    trucks: Mapped[list["Truck"]] = relationship(secondary=package_truck, back_populates="packages")
    
    
    
class Waybill(Base):
    __tablename__ = "waybill"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tracking_number: Mapped[str] = mapped_column(String(50), nullable=False, unique= True)
    shipping_status: Mapped[str] = mapped_column(String(20), nullable=False)
    
    package_id: Mapped[int] = mapped_column(ForeignKey("package.id"), unique=True)
    package: Mapped["Package"] = relationship(back_populates="waybill")
    
    
class Truck(Base):
    __tablename__ = "truck"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    license_plate: Mapped[str] = mapped_column(String(50), nullable=False, unique= True)
    packages: Mapped[list["Package"]] = relationship(secondary=package_truck, back_populates="trucks")
    
    
    