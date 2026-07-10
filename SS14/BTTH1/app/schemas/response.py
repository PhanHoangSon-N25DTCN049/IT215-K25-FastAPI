from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from fastapi import Request


class APIResponse(BaseModel):
    statusCode: int
    message: str
    error: Any = None
    data: Any = None
    path: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

def create_api_response(request: Request, status_code: int, message: str, data: Any = None, error: Any = None):
    return {
        "statusCode": status_code,
        "message": message,
        "error": error,
        "data": data,
        "path": request.url.path,
    }