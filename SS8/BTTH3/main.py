from fastapi import FastAPI, HTTPException, status, Request, Response
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from typing import Any, Literal

desks = [
    {"id": 1, "desk_number": "DSK-A-01", "zone": "Zone A - Quiet Space", "price_per_day": 150000.0, "status": "AVAILABLE"},
    {"id": 2, "desk_number": "DSK-B-02", "zone": "Zone B - Creative", "price_per_day": 200000.0, "status": "AVAILABLE"},
    {"id": 3, "desk_number": "DSK-C-03", "zone": "Zone C - Panoramic", "price_per_day": 250000.0, "status": "MAINTENANCE"}
]

bookings = [
    {
        "id": 1,
        "desk_id": 1,
        "customer_name": "Nguyen Van A",
        "booking_date": "2026-07-01",
        "payment_status": "PAID"
    }
]

app = FastAPI()

# --- CHUẨN HÓA RESPONSE & EXCEPTION ---

class ResponseAPI(BaseModel):
    status: str
    message: str
    data: Any | None = None
    error: Any | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    path: str
    
def api_response(request: Request, status: str, message: str, data: Any = None, error: Any = None):
    return {
        "status": status,
        "message": message,
        "data": data,
        "error": error,
        "path": request.url.path
    }
    
@app.exception_handler(StarletteHTTPException)
def Customer_HTTPException(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "Fail",
            "message": str(exc.detail),
            "data": None,
            "error": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )
    
@app.exception_handler(RequestValidationError)
def customer_requestValidate(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "Fail",
            "message": "Dữ liệu đầu vào không hợp lệ",
            "data": exc.errors(),
            "error": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

# --- SCHEMAS (Validation) ---

class DeskCreateUpdate(BaseModel):
    desk_number: str
    zone: str
    price_per_day: float = Field(gt=0)
    status: Literal["AVAILABLE", "UNAVAILABLE", "MAINTENANCE"]

class BookingCreate(BaseModel):
    desk_id: int
    customer_name: str
    booking_date: str
    payment_status: Literal["PENDING", "PAID", "CANCELLED"]

# --- ENDPOINTS: DESKS ---

@app.post("/desks", status_code=status.HTTP_201_CREATED)
def create_desk(request: Request, payload: DeskCreateUpdate):
    for desk in desks:
        if desk["desk_number"] == payload.desk_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Desk number đã tồn tại trên hệ thống")
    
    new_id = max([d["id"] for d in desks], default=0) + 1
    new_desk = {"id": new_id, **payload.model_dump()}
    desks.append(new_desk)
    
    return api_response(request, "Success", "Thêm bàn làm việc thành công", new_desk)

@app.get("/desks")
def get_desks(
    request: Request, 
    zone_keyword: str | None = None, 
    status: str | None = None, 
    max_price: float | None = None
):
    result = desks
    
    if zone_keyword:
        keyword_lower = zone_keyword.lower()
        result = [d for d in result if keyword_lower in d["zone"].lower()]
    
    if status:
        result = [d for d in result if d["status"] == status]
        
    if max_price is not None:
        result = [d for d in result if d["price_per_day"] <= max_price]
        
    return api_response(request, "Success", "Lấy danh sách bàn làm việc thành công", result)

@app.get("/desks/{desk_id}")
def get_desk(request: Request, desk_id: int):
    for desk in desks:
        if desk["id"] == desk_id:
            return api_response(request, "Success", "Lấy thông tin chi tiết bàn làm việc thành công", desk)
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desk not found")

@app.put("/desks/{desk_id}")
def update_desk(request: Request, desk_id: int, payload: DeskCreateUpdate):
    for idx, desk in enumerate(desks):
        if desk["id"] == desk_id:
            for d in desks:
                if d["id"] != desk_id and d["desk_number"] == payload.desk_number:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Desk number đã tồn tại trên hệ thống")
            
            updated_desk = {"id": desk_id, **payload.model_dump()}
            desks[idx] = updated_desk
            return api_response(request, "Success", "Cập nhật bàn làm việc thành công", updated_desk)
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desk not found")

@app.delete("/desks/{desk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_desk(desk_id: int):
    for idx, desk in enumerate(desks):
        if desk["id"] == desk_id:
            desks.pop(idx)
            # Trả về Response 204 No Content thuần, không kèm Body (không gọi api_response)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desk not found")

# --- ENDPOINTS: BOOKINGS ---

@app.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(request: Request, payload: BookingCreate):
    target_desk = next((d for d in desks if d["id"] == payload.desk_id), None)
    
    if not target_desk:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bàn làm việc không tồn tại trong danh mục")
    
    if target_desk["status"] != "AVAILABLE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bàn làm việc không ở trạng thái sẵn sàng cho thuê")
        
    for booking in bookings:
        if booking["desk_id"] == payload.desk_id and booking["booking_date"] == payload.booking_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vị trí này đã có người đặt trong ngày")
    
    new_id = max([b["id"] for b in bookings], default=0) + 1
    new_booking = {"id": new_id, **payload.model_dump()}
    bookings.append(new_booking)
    
    return api_response(request, "Success", "Đăng ký đặt chỗ thành công", new_booking)

@app.get("/bookings")
def get_bookings(request: Request):
    return api_response(request, "Success", "Lấy danh sách lịch sử đặt chỗ thành công", bookings)