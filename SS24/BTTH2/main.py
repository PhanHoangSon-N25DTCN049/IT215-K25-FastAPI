from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

app = FastAPI(title="FlashMove Logistics API")

origins = [
    "https://driver.flashmove.io",
    "https://hub.flashmove.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-Role-Identity"],
)

ENDPOINT_PERMISSIONS = {
    "/api/v1/orders/assign": ["DISPATCHER"],
    "/api/v1/orders/status": ["DISPATCHER", "DRIVER"],
    "/api/v1/orders/track": ["DISPATCHER", "DRIVER", "CUSTOMER_SUPPORT"]
}

class RBACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Lọc và chỉ kiểm tra các route thuộc API v1 của đơn hàng
        if path.startswith("/api/v1/orders/"):
            user_role = request.headers.get("X-Role-Identity")
            allowed_roles = ENDPOINT_PERMISSIONS.get(path, [])

            # Kiểm tra xem role của user có nằm trong danh sách cho phép không
            if not user_role or user_role not in allowed_roles:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"status": "Rejected", "reason": "Unauthorized action for this role"}
                )

        # Cho phép Request đi tiếp nếu hợp lệ
        response = await call_next(request)
        return response

app.add_middleware(RBACMiddleware)


@app.post("/api/v1/orders/assign")
async def assign_order():
    """Gán đơn hàng cho tài xế (Chỉ DISPATCHER)"""
    return {"status": "Success", "message": "Order assigned successfully"}

@app.patch("/api/v1/orders/status")
async def update_order_status():
    """Cập nhật trạng thái đơn (Chỉ DISPATCHER và DRIVER)"""
    return {"status": "Success", "message": "Order status updated successfully"}

@app.get("/api/v1/orders/track")
async def track_order():
    """Xem tiến trình đơn hàng (Cả 3 vai trò)"""
    return {"status": "Success", "message": "Tracking information retrieved"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)