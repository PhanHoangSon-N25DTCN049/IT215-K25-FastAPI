from app.database import Base
from sqlalchemy import String, Integer, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class Viewer(Base):
    __tablename__ = "viewer"
    
    viewer_id: Mapped[int] = mapped_column(Integer,primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    total_donated: Mapped[int] = mapped_column(Integer,default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    donation: Mapped[list["Donations"]] = relationship(back_populates="viewer")
    
class Donations(Base):
    __tablename__ = "donations"
    
    donation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    viewer_id: Mapped[int] = mapped_column(ForeignKey("viewer.viewer_id"))
    viewer: Mapped[Viewer] = relationship(back_populates="donations")
    message: Mapped[str] = mapped_column(String(1000))
    sepay_id: Mapped[int] = mapped_column(Integer, unique=True)
    amount: Mapped[int] = mapped_column(Integer, nullable= False)
    payment_code: Mapped[str] = mapped_column(String(50), nullable= False )
    is_displayed: Mapped[bool] = mapped_column(Boolean, nullable=False, default= False)
    
class PendingDonation(Base):
    __tablename__ = "pending"
    pending_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    viewer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    