from pydantic import BaseModel, EmailStr, Field



class UserCreate(BaseModel):
    email: EmailStr 
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2)

class TokenDataResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str 
    
class RefreshRequest(BaseModel):
    refresh_token: str