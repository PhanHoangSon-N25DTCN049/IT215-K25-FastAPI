from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class UserData(BaseModel):
    id: int 
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
        
