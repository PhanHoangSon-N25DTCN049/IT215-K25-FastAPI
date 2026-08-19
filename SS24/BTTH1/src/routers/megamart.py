from fastapi import APIRouter, Depends
from src.core.roles import UserRole
from src.middlewares.rbac import RoleChecker

router = APIRouter(tags=["MegaMart ERP"])

# Khởi tạo các RoleChecker theo từng cấp độ quyền hạn
allow_admin_and_hr = RoleChecker([UserRole.ADMIN, UserRole.HR])
allow_admin_only = RoleChecker([UserRole.ADMIN])
allow_all_staff = RoleChecker([UserRole.ADMIN, UserRole.HR, UserRole.STAFF])


@router.get(
    "/salary/modify",
    summary="Quản lý và chỉnh sửa bảng lương",
    dependencies=[Depends(allow_admin_and_hr)],
)
def modify_salary(user_role: UserRole = Depends(allow_admin_and_hr)):
    return {
        "message": "Truy cập thông tin và quản lý bảng lương thành công.",
        "accessible_by": ["ADMIN", "HR"],
        "requested_by": user_role.value,
    }


@router.get(
    "/system/settings",
    summary="Cấu hình hệ thống ERP",
    dependencies=[Depends(allow_admin_only)],
)
def get_system_settings(user_role: UserRole = Depends(allow_admin_only)):
    return {
        "message": "Truy cập cấu hình hệ thống tối mật của MegaMart thành công.",
        "accessible_by": ["ADMIN"],
        "requested_by": user_role.value,
        "settings": {
            "environment": "production",
            "db_cluster": "megamart-primary-cluster",
            "security_level": "high",
        },
    }


@router.get(
    "/profile",
    summary="Xem thông tin cá nhân của nhân viên",
    dependencies=[Depends(allow_all_staff)],
)
def get_profile(user_role: UserRole = Depends(allow_all_staff)):
    return {
        "message": "Truy cập thông tin hồ sơ cá nhân thành công.",
        "accessible_by": ["ADMIN", "HR", "STAFF"],
        "requested_by": user_role.value,
        "profile": {
            "employee_id": "EMP-009",
            "company": "MegaMart Global Retail",
            "role": user_role.value,
        },
    }
