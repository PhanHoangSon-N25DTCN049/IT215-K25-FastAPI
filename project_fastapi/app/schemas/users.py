from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserData(BaseModel):
    
    id: int 
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True 
        
