from fastapi import FastAPI, Depends, status, HTTPException, Request, exception_handlers
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
import models
from database import get_db
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
app = FastAPI()

class APIResponse(BaseModel):
    status: str
    message: str
    data: Any | None = None
    error: Any | None = None
    timestamps: str =  Field(default_factory=lambda: datetime.now().isoformat())
    path: str

def api_response(request:Request, status:str, message: str, data: Any = None, error: Any = None):
    return {
        "status":status,
        "message":message,
        "data": data,
        "error": error,
        "path": request.url.path
    }

@app.exception_handlers(RequestValidationError)
def custom_request_validate_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "fail",
            "message": "Dữ liệu truyền vào không hợp lệ",
            "data": exc.errors(),
            "error": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )
    
@app.exception_handlers(StarletteHTTPException)
def custom_request_HTTPException(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "fail",
            "message": str(exc.detail),
            "data": None,
            "error": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )
    
@app.get("/health", response_model=status.HTTP_200_OK, tags=["health"])
def get_health():
    return {
        "massage": "Server hoạt động bình thường"
    }

