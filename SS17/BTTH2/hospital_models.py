from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, Date, ForeignKey, Table, Column

class Base(DeclarativeBase):
    pass

patient_medication = Table(
    "patient_medication",
    Base.metadata,
    Column("patient_id", ForeignKey("patient.id"), primary_key=True),
    Column("medication_id", ForeignKey("medication.id"), primary_key=True),
)

class Doctor(Base):
    __tablename__ = "doctor"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(String(255), nullable=False)
    
    patients: Mapped[list["Patient"]] = relationship(back_populates="doctor")

class Patient(Base):
    __tablename__ = "patient"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctor.id"))
    
    doctor: Mapped["Doctor"] = relationship(back_populates="patients")
    
    insurance: Mapped["Insurance"] = relationship(back_populates="patient", uselist=False)
    
    medications: Mapped[list["Medication"]] = relationship(secondary=patient_medication, back_populates="patients")

class Insurance(Base):
    __tablename__ = "insurance"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    insurance_number: Mapped[str] = mapped_column(String(50), nullable=False)
    expiry_date: Mapped[Date] = mapped_column(Date, nullable=False)
    
    patient_id: Mapped[int] = mapped_column(ForeignKey("patient.id"), unique=True)
    
    patient: Mapped["Patient"] = relationship(back_populates="insurance")

class Medication(Base):
    __tablename__ = "medication"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    patients: Mapped[list["Patient"]] = relationship(secondary=patient_medication, back_populates="medications")