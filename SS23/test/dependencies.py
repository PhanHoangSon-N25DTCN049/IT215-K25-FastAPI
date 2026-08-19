from fastapi import Depends, HTTPException, status
from models import User
# Giả định hàm get_current_user đã được định nghĩa để giải mã JWT và lấy User từ DB
from security import get_current_user 


class RoleChecker:
    """
    Sử dụng cơ chế Parameterized Dependency để kiểm tra quyền truy cập động.
    """
    def __init__(self, allowed_roles: list[str]):
        # Nhận vào danh sách các vai trò được phép truy cập endpoint
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        # Kiểm tra xem vai trò của người dùng hiện tại có nằm trong danh sách cho phép không
        if current_user.role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quyền truy cập bị từ chối. Endpoint này yêu cầu các vai trò: {', '.join(self.allowed_roles)}"
            )

        # Trả về đối tượng user hợp lệ để endpoint có thể sử dụng nếu cần
        return current_user
