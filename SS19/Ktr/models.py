from sqlalchemy import String, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base, engine

class Clinic(Base):
    __tablename__ = "clinics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  
    clinic_name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    
    doctors: Mapped[list["Doctor"]] = relationship(back_populates="clinic")
    
class Doctor(Base):
    __tablename__ = "doctors"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  
    doctor_code: Mapped[str] = mapped_column(String(20), nullable= False, unique=True)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"), )
    
    clinic: Mapped["Clinic"] = relationship(back_populates="doctors")
    license: Mapped["License"] = relationship(back_populates="doctor", uselist=False)
    
    
class License(Base):
    __tablename__  = "license"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  
    license_number: Mapped[str] = mapped_column(String(30), nullable= False, unique=True)
    issue_by: Mapped[str] = mapped_column(String(100), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), unique=True)
    
    doctor: Mapped["Doctor"] = relationship(back_populates="license")

Base.metadata.create_all(bind=engine)