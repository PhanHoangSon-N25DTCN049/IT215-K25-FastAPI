from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base, engine

class Students(Base):
    __tablename__= "students"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(nullable=False)
    class_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    phone_number: Mapped[str] = mapped_column(nullable=False)
    
Base.metadata.create_all(engine)