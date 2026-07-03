from fastapi import FastAPI, HTTPException, status, Request
from pydantic import BaseModel, Field, EmailStr
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from typing import Any, Literal

assets = [
    {"id": 1, "serial_number": "SN-MAC-01", "model": "MacBook Pro M3", "stock_available": 5, "status": "READY"},
    {"id": 2, "serial_number": "SN-DELL-02", "model": "Dell UltraSharp 27", "stock_available": 10, "status": "READY"},
    {"id": 3, "serial_number": "SN-THINK-03", "model": "ThinkPad X1 Carbon", "stock_available": 0, "status": "REPAIRING"}
]

allocations = [
    {
        "id": 1,
        "asset_id": 1,
        "employee_email": "dev.nguyen@company.com",
        "allocated_quantity": 1,
        "start_date": "2026-07-01",
        "duration_months": 12
    }
]

app = FastAPI()

class ResponseAPI(BaseModel):
    status: str
    message:str
    data: Any | None = None
    error: Any | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    path: str
    
def api_response(request: Request, status:str, message:str, data: Any = None, error: Any = None):
    return {
        "status":status,
        "message": message,
        "data": data,
        "error": error,
        "path": request.url.path
    }
    
@app.exception_handler(StarletteHTTPException)
def Customer_HTTPException(request: Request, exc:StarletteHTTPException):
    return JSONResponse (
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
def customer_requestValidate(request: Request, exc:RequestValidationError):
    return JSONResponse (
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
    
class AssetCreateUpdate(BaseModel):
    serial_number: str
    model: str = Field(min_length=2, max_length=255)
    stock_available: int = Field(ge=0)
    status: Literal["READY", "ALLOCATED", "REPAIRING", "SCRAPPED"]

class AllocationCreate(BaseModel):
    asset_id: int
    employee_email: EmailStr 
    allocated_quantity: int = Field(gt=0)
    start_date: str
    duration_months: int = Field(ge=1, le=12)

# --- ENDPOINTS: ASSETS ---

@app.post("/assets", status_code=status.HTTP_201_CREATED)
def create_asset(request: Request, payload: AssetCreateUpdate):
    for asset in assets:
        if asset["serial_number"] == payload.serial_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Serial number đã tồn tại trên hệ thống")
    
    new_id = max([a["id"] for a in assets], default=0) + 1
    new_asset = {"id": new_id, **payload.model_dump()}
    assets.append(new_asset)
    
    return api_response(request, "Success", "Khai báo tài sản thành công", new_asset)

@app.get("/assets")
def get_assets(
    request: Request, 
    keyword: str | None = None, 
    status: str | None = None, 
    min_stock: int | None = None
):
    result = assets
    
    if keyword:
        keyword_lower = keyword.lower()
        result = [a for a in result if keyword_lower in a["serial_number"].lower() or keyword_lower in a["model"].lower()]
    
    if status:
        result = [a for a in result if a["status"] == status]
        
    if min_stock is not None:
        result = [a for a in result if a["stock_available"] >= min_stock]
        
    return api_response(request, "Success", "Lấy danh mục tài sản thành công", result)

@app.get("/assets/{asset_id}")
def get_asset(request: Request, asset_id: int):
    for asset in assets:
        if asset["id"] == asset_id:
            return api_response(request, "Success", "Lấy thông tin tài sản thành công", asset)
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

@app.put("/assets/{asset_id}")
def update_asset(request: Request, asset_id: int, payload: AssetCreateUpdate):
    for idx, asset in enumerate(assets):
        if asset["id"] == asset_id:
            for a in assets:
                if a["id"] != asset_id and a["serial_number"] == payload.serial_number:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Serial number đã tồn tại trên hệ thống")
            
            updated_asset = {"id": asset_id, **payload.model_dump()}
            assets[idx] = updated_asset
            return api_response(request, "Success", "Cập nhật tài sản thành công", updated_asset)
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

@app.delete("/assets/{asset_id}")
def delete_asset(request: Request, asset_id: int):
    for idx, asset in enumerate(assets):
        if asset["id"] == asset_id:
            deleted_asset = assets.pop(idx)
            return api_response(request, "Success", "Xóa tài sản thành công", deleted_asset)
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")


@app.post("/allocations", status_code=status.HTTP_201_CREATED)
def create_allocation(request: Request, payload: AllocationCreate):
    target_asset = next((a for a in assets if a["id"] == payload.asset_id), None)
    if not target_asset:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thiết bị không tồn tại trong danh mục")
    
    if target_asset["status"] != "READY":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thiết bị không ở trạng thái READY")
        
    if payload.allocated_quantity > target_asset["stock_available"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Số lượng yêu cầu vượt quá số lượng tồn kho khả dụng")
        
    target_asset["stock_available"] -= payload.allocated_quantity
    
    new_id = max([a["id"] for a in allocations], default=0) + 1
    new_allocation = {"id": new_id, **payload.model_dump()}
    allocations.append(new_allocation)
    
    return api_response(request, "Success", "Cấp phát thiết bị thành công", new_allocation)

@app.get("/allocations")
def get_allocations(request: Request):
    return api_response(request, "Success", "Lấy danh sách lịch sử cấp phát thành công", allocations)