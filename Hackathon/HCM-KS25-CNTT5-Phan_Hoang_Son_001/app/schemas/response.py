from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
from fastapi import Request
from fastapi.encoders import jsonable_encoder
class APIResponse(BaseModel):
    statusCode: int
    message: str
    data: Any
    error: Any
    path: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
def api_response(request: Request, statusCode: int, message: str, data: Any = None, error: Any = None):
    return {
        "statusCode": statusCode,
        "message": message,
        "data": jsonable_encoder(data) if data is not None else None,
        "error": jsonable_encoder(error) if error is not None else None,
        "path": request.url.path
    }
    