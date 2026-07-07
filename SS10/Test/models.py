from database import Base
from sqlalchemy import Boolean, String, Integer, Column

class parking_slots(Base):
    __tablename__ = "parking_slots"
    
    id = Column(Integer, autoincrement=True, primary_key=True)
    slot_code = Column(String(50), unique= True, nullable=False)
    zone_name = Column(String(255), nullable=False)
    max_weight = Column(Integer, nullable=False)
    is_available = Column(Boolean, default=True)
    
