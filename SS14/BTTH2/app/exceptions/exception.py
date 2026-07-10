from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI, Request, status
from datetime import datetime
from http import HTTPStatus

def setup_handler(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    def customer_http_exception(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content= {
                "statusCode":exc.status_code,
                "message":exc.detail,
                "error":HTTPStatus(exc.status_code).phrase,
                "data": None,
                "path": request.url.path,
                "timestamp": datetime.now().isoformat()
            }   
        )
    @app.exception_handler(RequestValidationError)
    def customer_response_validate_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "statusCode":status.HTTP_422_UNPROCESSABLE_CONTENT,
                "message": "Lỗi dữ liệu đầu vào",
                "error":str(exc.errors()),
                "data": None,
                "path": request.url.path,
                "timestamp": datetime.now().isoformat()
            } 
        )
    
