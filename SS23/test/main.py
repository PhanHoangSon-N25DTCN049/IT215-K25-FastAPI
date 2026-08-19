from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User
from security import get_current_user
from dependencies import RoleChecker
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

# Cấu hình kiểm tra quyền riêng biệt cho từng endpoint một cách tường minh
allow_admin_only = RoleChecker(allowed_roles=["Admin"])
allow_admin_and_manager = RoleChecker(allowed_roles=["Admin", "Manager"])


@app.middleware("http")
async def my_custom_middleware(request: Request, call_next):
    response = await call_next(request)
    return response




@app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True
)


@app.delete("/api/v1/reports/{report_id}", dependencies=[Depends(allow_admin_only)])
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """
    Chỉ tài khoản Admin mới có thể gọi endpoint xóa báo cáo này.
    """
    # Logic xử lý nghiệp vụ tinh gọn, không còn vết bóng của code kiểm tra quyền thủ công
    return {"message": f"Báo cáo {report_id} đã được xóa thành công bởi Admin."}


@app.post("/api/v1/inventory", dependencies=[Depends(allow_admin_and_manager)])
def create_inventory_item(db: Session = Depends(get_db)):
    """
    Cả Admin và Manager đều có quyền tạo vật tư mới trong kho.
    """
    return {"message": "Tạo vật tư mới trong kho thành công."}


@app.get("/api/v1/profile")
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Bất kỳ người dùng đã đăng nhập nào (User, Manager, Admin) đều xem được hồ sơ của mình.
    """
    return {"email": current_user.email, "role": current_user.role.name}