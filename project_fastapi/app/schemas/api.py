from pydantic import BaseModel, Field
from fastapi import Request
from typing import Any
from datetime import datetime

class ApiResponse[T](BaseModel):
    statusCode: int
    message: str
    data: T | None = None
    error: Any | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    path: str

    
def api_response(request: Request, statusCode: int, message: str, data: Any = None, error: Any = None):
    return{
        "statusCode": statusCode,
        "message": message,
        "data": data,
        "error": error,
        "path": request.url.path
    }