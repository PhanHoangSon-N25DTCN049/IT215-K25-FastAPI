import time
import uuid
import logging
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
import uvicorn

# ==========================================
# 1. CẤU HÌNH CƠ BẢN & SECRET KEY
# ==========================================
SECRET_KEY = "my_super_secret_key_12345"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dummy Database người dùng
FAKE_USERS_DB = {
    "user1": {"username": "user1", "role": "user", "is_active": True},
    "admin1": {"username": "admin1", "role": "admin", "is_active": True},
    "banned1": {"username": "banned1", "role": "user", "is_active": False},
}

# ==========================================
# 2. MIDDLEWARE GIÁM SÁT REQUEST (GHI LOG & ĐO THỜI GIAN)
# ==========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_monitor")

class RequestTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Bỏ qua không kiểm tra request OPTIONS (dùng cho CORS Preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Chuyển tiếp request cho ứng dụng xử lý
        response = await call_next(request)
        
        # Tính toán thời gian và gắn Headers
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        # Ghi log
        logger.info(f"Method: {request.method} | URL: {request.url.path} | Status: {response.status_code} | Time: {process_time:.4f}s | ReqID: {request_id}")
        
        return response

# ==========================================
# 3. BẢO MẬT & JWT & PHÂN QUYỀN (DEPENDENCIES)
# ==========================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def create_access_token(data: dict):
    """Hàm tạo JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Giải mã Token và lấy thông tin User hiện tại"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token missing sub claim")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
        
    user = FAKE_USERS_DB.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Inactive user")
        
    return user

def require_admin(current_user: dict = Depends(get_current_user)):
    """Chỉ Admin mới được truy cập"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user

class RequireOwnership:
    """Kiểm tra quyền sở hữu dữ liệu: Admin xem hết, User chỉ xem của mình"""
    def __call__(self, target_user_id: str, current_user: dict = Depends(get_current_user)):
        if current_user["role"] == "admin":
            return current_user
        if current_user["username"] != target_user_id:
            raise HTTPException(status_code=403, detail="You can only access your own data")
        return current_user

# ==========================================
# 4. ROUTERS (API ENDPOINTS)
# ==========================================
auth_router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
resource_router = APIRouter(prefix="/api/v1/resources", tags=["Resources"])

# --- Nhóm 1: Xác thực ---
@auth_router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = FAKE_USERS_DB.get(form_data.username)
    # Giả lập mật khẩu chung là 'password'
    if not user or form_data.password != "password":
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

# --- Nhóm 2 & Nhóm 3: Tài nguyên & Phân quyền ---
@resource_router.get("/")
def get_resources(user: dict = Depends(get_current_user)):
    """User & Admin đều xem được"""
    return {"message": "Resource list", "requested_by": user["username"]}

@resource_router.post("/")
def create_resource(user: dict = Depends(require_admin)):
    """Chỉ Admin được tạo"""
    return {"message": "Resource created successfully"}

@resource_router.delete("/{res_id}")
def delete_resource(res_id: int, user: dict = Depends(require_admin)):
    """Chỉ Admin được xóa"""
    return {"message": f"Resource {res_id} deleted"}

@resource_router.get("/users/{target_user_id}/submissions")
def get_user_submissions(target_user_id: str, user: dict = Depends(RequireOwnership())):
    """User chỉ lấy được bài nộp của chính mình, Admin lấy được của mọi người"""
    return {"message": f"Submissions of {target_user_id}"}

# ==========================================
# 5. KHỞI TẠO APP & GẮN MIDDLEWARE/ROUTER
# ==========================================
app = FastAPI(title="Secure Learning Portal API")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Thay bằng domain frontend thực tế (Không dùng '*')
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn Custom Middleware
app.add_middleware(RequestTrackingMiddleware)

# Đăng ký Router
app.include_router(auth_router)
app.include_router(resource_router)

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "System is running perfectly"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)