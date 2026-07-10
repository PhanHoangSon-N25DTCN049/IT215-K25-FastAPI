from app.database import Base, engine
from sqlalchemy.orm import Mapped, mapped_column


class Students(Base):
    __tablename__ = "students"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(nullable= False)
    email: Mapped[str] = mapped_column(nullable= False)
    major: Mapped[str] = mapped_column(nullable= False)
    gpa: Mapped[float] = mapped_column(nullable= False)
    
Base.metadata.create_all(engine)

