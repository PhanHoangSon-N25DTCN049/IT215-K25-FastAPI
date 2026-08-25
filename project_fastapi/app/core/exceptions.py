from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from http import HTTPStatus
from datetime import datetime





class AppException(Exception):
    """Lớp Exception cơ sở cho toàn bộ ứng dụng."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, headers: dict = None):
        self.message = message
        self.status_code = status_code
        self.headers = headers
        super().__init__(self.message)


class NotFoundException(AppException):
    """Ngoại lệ khi không tìm thấy tài nguyên (404)."""

    def __init__(self, message: str = "Tài nguyên không tìm thấy"):
        super().__init__(message=message, status_code=status.HTTP_404_NOT_FOUND)


class BadRequestException(AppException):
    """Ngoại lệ khi yêu cầu không hợp lệ (400)."""

    def __init__(self, message: str = "Yêu cầu không hợp lệ"):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedException(AppException):
    """Ngoại lệ khi chưa xác thực danh tính (401)."""

    def __init__(self, message: str = "Chưa xác thực hoặc thông tin xác thực không đúng", headers: dict = None):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED, headers=headers)


class ForbiddenException(AppException):
    """Ngoại lệ khi không có quyền truy cập (403)."""

    def __init__(self, message: str = "Bạn không có quyền thực hiện hành động này"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(AppException):
    """Ngoại lệ khi xảy ra xung đột dữ liệu (409)."""

    def __init__(self, message: str = "Tài nguyên đã tồn tại hoặc có xung đột"):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)



class InvalidInputException(AppException):
    """Ngoại lệ khi dữ liệu đầu vào không hợp lệ (422)."""
    def __init__(self, message: str = "Dữ liệu đầu vào không hợp lệ"):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class TooManyRequestsException(AppException):
    """Ngoại lệ khi vượt quá tần suất yêu cầu cho phép (429)."""
    def __init__(self, message: str = "Bạn đã thực hiện quá nhiều yêu cầu. Vui lòng thử lại sau!"):
        super().__init__(message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    def customize_http_exc(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "statusCode": exc.status_code,
                "message": exc.detail,
                "data": None,
                "error": HTTPStatus(exc.status_code).phrase,
                "path": request.url.path,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    @app.exception_handler(AppException)
    def customize_app_exc(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "statusCode": exc.status_code,
                "message": exc.message,
                "data": None,
                "error": HTTPStatus(exc.status_code).phrase,
                "path": request.url.path,
                "timestamp": datetime.now().isoformat()
            },
            headers=exc.headers
        )
            
    @app.exception_handler(RequestValidationError)
    def customize_request_validate_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "statusCode": 422,
                "message": "Lỗi dữ liệu đầu vào",
                "data": None,
                "error": exc.errors(),
                "path": request.url.path,
                "timestamp": datetime.now().isoformat()
            }
        )

    from slowapi.errors import RateLimitExceeded

    @app.exception_handler(RateLimitExceeded)
    def customize_rate_limit_exceeded_error(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "statusCode": 429,
                "message": f"Bạn đã thử quá số lần cho phép ({exc.detail}). Vui lòng thử lại sau!",
                "data": None,
                "error": HTTPStatus(429).phrase,
                "path": request.url.path,
                "timestamp": datetime.now().isoformat()
            }
        )