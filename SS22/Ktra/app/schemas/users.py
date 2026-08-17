from pydantic import BaseModel, Field
from fastapi import Request
from datetime import datetime
from typing import Any, Literal
from app.models import UserRole


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    role: Literal["CUSTOMER", "ADMIN"] | None = "CUSTOMER"
    
class UserLoginRequest(BaseModel):
    username: str
    password: str
    
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    
class TransferRequest(BaseModel):
    to_username:str
    amount: float = Field(gt=0)
    note: str

class UserResponse(BaseModel):
    id: int
    username:str
    role:str
    balance: float
    created_at: datetime

class APIResponse(BaseModel):
    statusCode: int
    message: str
    data: Any | None = None
    error: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    path: str

def api_response(request: Request, statusCode, message, data = None, error = None):
    return APIResponse(
        statusCode= statusCode,
        message= message,
        data= data,
        error=error,
        path= request.url.path
    )