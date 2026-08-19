from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Lớp Exception cơ sở cho toàn bộ ứng dụng."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
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

    def __init__(self, message: str = "Chưa xác thực hoặc thông tin xác thực không đúng"):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    """Ngoại lệ khi không có quyền truy cập (403)."""

    def __init__(self, message: str = "Bạn không có quyền thực hiện hành động này"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


class ConflictException(AppException):
    """Ngoại lệ khi xảy ra xung đột dữ liệu (409)."""

    def __init__(self, message: str = "Tài nguyên đã tồn tại hoặc có xung đột"):
        super().__init__(message=message, status_code=status.HTTP_409_CONFLICT)


class PermissionDeniedException(AppException):
    """Ngoại lệ khi người dùng không đủ quyền truy cập (403)."""

    def __init__(self, message: str = "Permission Denied"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


# Specific Model Exceptions (Ví dụ cụ thể cho Item)
class ItemNotFoundException(NotFoundException):
    def __init__(self, item_id: int):
        super().__init__(message=f"Không tìm thấy Item có ID là {item_id}")


def setup_exception_handlers(app: FastAPI) -> None:
    """Đăng ký các custom exception handlers cho FastAPI application."""

    @app.exception_handler(PermissionDeniedException)
    async def permission_denied_handler(request: Request, exc: PermissionDeniedException):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": exc.message},
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_type": exc.__class__.__name__,
                "message": exc.message,
                "path": request.url.path,
            },
        )
