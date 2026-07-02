from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime

app = FastAPI()

# Dữ liệu ban đầu
orders_db = [
    {"id": 1, "code": "SP001", "status": "PENDING"},
    {"id": 2, "code": "SP002", "status": "DELIVERED"}
]

def create_unified_response(status_code: int, message: str, data: any, error: any, path: str):
    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "message": message,
            "data": data,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "path": path
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return create_unified_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Dữ liệu đầu vào không hợp lệ",
        data=None,
        error=exc.errors(),
        path=request.url.path
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return create_unified_response(
        status_code=exc.status_code,
        message=exc.detail, 
        data=None,
        error="Lỗi nghiệp vụ",
        path=request.url.path
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return create_unified_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Hệ thống đang gặp sự cố nội bộ. Vui lòng thử lại sau.",
        data=None,
        error="Internal Server Error",
        path=request.url.path
    )


@app.delete("/orders/{order_id}")
async def cancel_order(order_id: int, request: Request):
    order = next((o for o in orders_db if o["id"] == order_id), None)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Không tìm thấy đơn hàng"
        )
        
    if order["status"] == "DELIVERED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Đơn hàng đã được giao, không thể hủy"
        )
        
    order["status"] = "CANCELLED"
    
    return {
        "statusCode": status.HTTP_200_OK,
        "message": "Hủy đơn hàng thành công",
        "data": order,
        "error": None,
        "timestamp": datetime.now().isoformat(),
        "path": request.url.path
    }