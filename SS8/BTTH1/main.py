from fastapi import FastAPI, Query, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Any
from datetime import datetime, timezone

# Dữ liệu mẫu chính xác từ bài thực hành
carriers = [
    {"id": 1, "code": "GHN", "name": "Giao Hang Nhanh", "max_weight_capacity": 5000, "status": "ACTIVE"},
    {"id": 2, "code": "GHTK", "name": "Giao Hang Tiet Kiem", "max_weight_capacity": 3000, "status": "ACTIVE"},
    {"id": 3, "code": "VTP", "name": "Viettel Post", "max_weight_capacity": 10000, "status": "SUSPENDED"}
]

shipments = [
    {
        "id": 1,
        "carrier_id": 1,
        "order_reference": "ORD-2026-001",
        "total_weight": 4200,
        "dispatch_date": "2026-07-01",
        "shift": "MORNING"
    }
]

app = FastAPI()

# 1. Định nghĩa Schema phản hồi chung
class ResponseAPI(BaseModel):
    status: str
    message: str
    data: Any | None = None
    error: Any | None = None
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    path: str

# 2. Hàm tiện ích cho phản hồi thành công
def success_response(request: Request, message: str, data: Any = None) -> dict:
    return {
        "status": "success",
        "message": message,
        "data": data,
        "error": None,
        "path": request.url.path
    }

# 3. Bộ xử lý ngoại lệ toàn cục (Exception Handlers)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": str(exc.detail),
            "data": None,
            "error": exc.status_code,
            "date": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Dữ liệu đầu vào không hợp lệ",
            "data": exc.errors(),
            "error": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "date": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path
        }
    )

# 4. Schemas yêu cầu đầu vào dữ liệu (Request Validation)
class RequestCarrier(BaseModel):
    code: str
    name: str = Field(..., min_length=3)
    max_weight_capacity: int = Field(..., gt=0)
    status: Literal["ACTIVE", "INACTIVE", "SUSPENDED"]

    @field_validator("code", "name")
    @classmethod
    def validate_string(cls, value: str, info):
        temp = value.strip()
        if not temp:
            raise ValueError(f"{info.field_name} không được để trống hoặc chỉ chứa khoảng trắng")
        return temp

class RequestShipment(BaseModel):
    carrier_id: int
    order_reference: str
    total_weight: int = Field(..., gt=0)
    dispatch_date: str
    shift: Literal["MORNING", "AFTERNOON", "NIGHT"]

    @field_validator("order_reference", "dispatch_date")
    @classmethod
    def validate_string(cls, value: str, info):
        temp = value.strip()
        if not temp:
            raise ValueError(f"{info.field_name} không được để trống hoặc chỉ chứa khoảng trắng")
        return temp

# ----------------- CARRIERS API -----------------

@app.get("/carriers", response_model=ResponseAPI)
def get_carriers(
    request: Request,
    keyword: str | None = None,
    status_filter: Literal["ACTIVE", "INACTIVE", "SUSPENDED"] | None = Query(default=None, alias="status"),
    min_weight: int | None = Query(default=None, gt=0)
):
    list_carriers = carriers
    
    if keyword:
        kw = keyword.lower()
        list_carriers = [c for c in list_carriers if kw in c["name"].lower() or kw in c["code"].lower()]
        
    if status_filter:
        list_carriers = [c for c in list_carriers if c["status"] == status_filter]
        
    if min_weight:
        list_carriers = [c for c in list_carriers if c["max_weight_capacity"] >= min_weight]

    return success_response(request, "Danh sách đối tác vận chuyển tìm thấy", list_carriers)


@app.get("/carriers/{carrier_id}", response_model=ResponseAPI)
def get_carrier_by_id(carrier_id: int, request: Request):
    carrier = next((c for c in carriers if c["id"] == carrier_id), None)
    if not carrier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrier not found")
        
    return success_response(request, "Thông tin chi tiết đối tác vận chuyển", carrier)


@app.post("/carriers", response_model=ResponseAPI, status_code=status.HTTP_201_CREATED)
def create_carrier(carrier: RequestCarrier, request: Request):
    if any(c["code"] == carrier.code for c in carriers):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mã đối tác (code) đã tồn tại")
        
    new_carrier = {
        "id": max((c["id"] for c in carriers), default=0) + 1,
        "code": carrier.code,
        "name": carrier.name,
        "max_weight_capacity": carrier.max_weight_capacity,
        "status": carrier.status
    }
    carriers.append(new_carrier)
    
    return success_response(request, "Thêm đối tác vận chuyển thành công", new_carrier)


@app.put("/carriers/{carrier_id}", response_model=ResponseAPI)
def update_carrier(carrier_id: int, carrier: RequestCarrier, request: Request):
    carrier_update = next((c for c in carriers if c["id"] == carrier_id), None)
    if not carrier_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrier not found")
        
    if any(c["code"] == carrier.code and c["id"] != carrier_id for c in carriers):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mã đối tác cập nhật đã tồn tại ở đơn vị khác")
        
    carrier_update.update(carrier.model_dump())
    
    return success_response(request, "Cập nhật thông tin đối tác thành công", carrier_update)


@app.delete("/carriers/{carrier_id}", response_model=ResponseAPI)
def delete_carrier(carrier_id: int, request: Request):
    carrier = next((c for c in carriers if c["id"] == carrier_id), None)
    if not carrier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrier not found")
        
    carriers.remove(carrier)
    
    return success_response(request, "Xóa đối tác vận chuyển thành công")


# ----------------- SHIPMENTS API -----------------

@app.get("/shipments", response_model=ResponseAPI)
def get_shipments(request: Request):
    return success_response(request, "Xem toàn bộ danh sách các chuyến giao hàng", shipments)


@app.post("/shipments", response_model=ResponseAPI, status_code=status.HTTP_201_CREATED)
def create_shipment(shipment: RequestShipment, request: Request):
    carrier = next((c for c in carriers if c["id"] == shipment.carrier_id), None)
    
    if not carrier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrier không tồn tại")
        
    if carrier["status"] != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Đối tác vận chuyển được chọn phải có trạng thái hoạt động là status = 'ACTIVE'")
        
    if shipment.total_weight > carrier["max_weight_capacity"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Khối lượng chuyến hàng vượt quá năng lực vận chuyển tối đa")
        
    is_conflict = any(
        s["carrier_id"] == shipment.carrier_id and 
        s["dispatch_date"] == shipment.dispatch_date and 
        s["shift"] == shipment.shift 
        for s in shipments
    )
    
    if is_conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Đối tác vận chuyển không được xếp trùng lịch điều phối chuyến hàng trên cùng một ngày và cùng ca làm việc")
        
    new_shipment = {
        "id": max((s["id"] for s in shipments), default=0) + 1,
        "carrier_id": shipment.carrier_id,
        "order_reference": shipment.order_reference,
        "total_weight": shipment.total_weight,
        "dispatch_date": shipment.dispatch_date,
        "shift": shipment.shift
    }
    shipments.append(new_shipment)
    
    return success_response(request, "Khởi tạo chuyến giao hàng mới thành công", new_shipment)