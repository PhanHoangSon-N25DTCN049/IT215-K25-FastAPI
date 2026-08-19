from typing import List, Optional, Set
from fastapi import Request, Header, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.roles import UserRole
from src.exceptions import PermissionDeniedException


# Bảng ánh xạ route pattern -> Các Roles được phép truy cập cho Middleware tập trung
ROUTE_PERMISSIONS = {
    "/api/v1/system/settings": {UserRole.ADMIN},
    "/api/v1/salary/modify": {UserRole.ADMIN, UserRole.HR},
    "/api/v1/profile": {UserRole.ADMIN, UserRole.HR, UserRole.STAFF},
}


class RoleChecker:
    """
    Callable Class đóng vai trò Dependency kiểm tra quyền hạn (Role-based Access Control).
    
    Cách sử dụng:
        require_admin = RoleChecker([UserRole.ADMIN])
        
        @router.get("/admin-only", dependencies=[Depends(require_admin)])
        def admin_endpoint(current_role: UserRole = Depends(require_admin)):
            ...
    """

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles: Set[UserRole] = set(allowed_roles)

    def __call__(
        self,
        x_user_role: Optional[str] = Header(
            None,
            alias="X-User-Role",
            description="Header xác định vai trò người dùng (ADMIN, HR, STAFF)",
        ),
    ) -> UserRole:
        if not x_user_role:
            raise PermissionDeniedException(message="Permission Denied")

        try:
            role = UserRole(x_user_role.strip().upper())
        except ValueError:
            raise PermissionDeniedException(message="Permission Denied")

        if role not in self.allowed_roles:
            raise PermissionDeniedException(message="Permission Denied")

        return role


def require_roles(*allowed_roles: UserRole) -> RoleChecker:
    """Helper function khởi tạo RoleChecker nhanh chóng."""
    return RoleChecker(list(allowed_roles))


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Middleware phân quyền tập trung (Role-Based Access Control).
    Kiểm tra quyền truy cập của người dùng dựa trên header X-User-Role trước khi tới Router.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Tìm kiếm quyền tương ứng với path
        allowed_roles: Optional[Set[UserRole]] = None
        for route_pattern, roles in ROUTE_PERMISSIONS.items():
            if path == route_pattern or path.startswith(f"{route_pattern}/"):
                allowed_roles = roles
                break

        # Nếu route cần bảo vệ
        if allowed_roles is not None:
            user_role_raw = request.headers.get("X-User-Role")

            # Nếu không có header hoặc role không hợp lệ
            if not user_role_raw:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Permission Denied"},
                )

            # Chuẩn hóa role sang Enum
            try:
                user_role = UserRole(user_role_raw.strip().upper())
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Permission Denied"},
                )

            # Kiểm tra xem user_role có trong danh sách được phép không
            if user_role not in allowed_roles:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"error": "Permission Denied"},
                )

        return await call_next(request)
