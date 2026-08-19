from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# Bẫy 2: Cấu hình CORS xử lý OPTIONS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy Secret & Mock Token Decryptor
SECRET_KEY = "supersecret"

def decode_dummy_token(token: str):
    # Mock JWT Decoder: user_token -> {"id": "user", "role": "user"}
    if token == "admin_token": return {"id": "admin_01", "role": "admin"}
    if token == "student01_token": return {"id": "student01", "role": "user"}
    if token == "student02_token": return {"id": "student02", "role": "user"}
    raise ValueError("Invalid token")

# ================= MIDDLEWARE (AUTHENTICATION) =================
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Bẫy 2: Bỏ qua kiểm tra JWT cho OPTIONS request
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Bỏ qua endpoint công khai
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Trích xuất và xác thực Token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid token"}
            )
        
        token = auth_header.split(" ")[1]
        try:
            user_payload = decode_dummy_token(token)
            request.state.user = user_payload  # Gắn user vào state
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Expired or invalid token"}
            )

        return await call_next(request)

app.add_middleware(AuthMiddleware)

# ================= DEPENDENCIES (AUTHORIZATION) =================
def get_current_user(request: Request):
    return request.state.user

def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

# Bẫy 4: Kiểm tra quyền sở hữu dữ liệu (User chỉ xem của mình, Admin xem tất cả)
def require_ownership_or_admin(target_user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        return current_user
    if current_user.get("id") != target_user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to access this user's data")
    return current_user

# ================= ENDPOINTS =================
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/exams")
def get_exams(user: dict = Depends(get_current_user)):
    return {"message": "Exam list", "user": user["id"]}

# Admin endpoints (Bẫy 3: Đã gắn Dependency chặt chẽ)
@app.post("/admin/exams")
def create_exam(user: dict = Depends(require_admin)):
    return {"message": "Exam created"}

@app.get("/admin/results")
def get_all_results(user: dict = Depends(require_admin)):
    return {"message": "All results data"}

# Bẫy 1: Xử lý Path Parameter gọn gàng qua Endpoint, không cần Regex ở Middleware
@app.patch("/admin/exams/{exam_id}/lock")
def lock_exam(exam_id: int, user: dict = Depends(require_admin)):
    return {"message": f"Exam {exam_id} locked"}

# Endpoint yêu cầu kiểm tra sở hữu dữ liệu (Bẫy 4)
@app.get("/users/{target_user_id}/results")
def get_user_results(target_user_id: str, user: dict = Depends(require_ownership_or_admin)):
    return {"message": f"Results for {target_user_id}"}