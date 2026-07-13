from fastapi import FastAPI, Request, status
from fastapi.exceptions import ResponseValidationError
from starlette.exceptions import HTTPException as StarletteHTTPExceptions
from fastapi.responses import JSONResponse
from http import HTTPStatus
from datetime import datetime

def customer_exception(app: FastAPI):
    @app.exception_handler(StarletteHTTPExceptions)
    def customer_http_exception(request: Request, exc: StarletteHTTPExceptions):
        return JSONResponse(
            status_code= exc.status_code,
            content={
                "statusCode": exc.status_code,
                "message": exc.detail,
                "error": HTTPStatus(exc.status_code).phrase,
                "data": None,
                "path": request.url.path
            }
        )
    @app.exception_handler(ResponseValidationError)
    def customer_validate_err(request: Request, exc: ResponseValidationError):
        return JSONResponse(
            status_code= status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "statusCode": status.HTTP_422_UNPROCESSABLE_CONTENT,
                "message": "Dữ liệu truyền vào không hợp lệ",
                "error": str(exc.errors()),
                "data": None,
                "path": request.url.path
            }
        )