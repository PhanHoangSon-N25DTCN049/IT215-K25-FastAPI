from database import Base
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

class StationTypesModel(Base):
    __tablename__ = "station_types"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    station: Mapped[List["StationsModel"]] = relationship(back_populates="station_type")
    
class StationsModel(Base):
    __tablename__ = "stations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    price_per_kwh: Mapped[int] = mapped_column(Integer, nullable=False)
    
    station_type_id: Mapped[int] = mapped_column(ForeignKey("station_types.id"))
    station_type: Mapped["StationTypesModel"] = relationship(back_populates="station")