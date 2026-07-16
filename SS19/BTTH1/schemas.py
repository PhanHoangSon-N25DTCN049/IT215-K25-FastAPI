from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# --- SCHEMAS FOR PACKAGE ---
class PackageBase(BaseModel):
    package_code: str
    weight: float
    warehouse_id: int

class PackageDetail(PackageBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PackageUpdate(BaseModel):
    package_code: Optional[str] = None
    weight: Optional[float] = None
    warehouse_id: Optional[int] = None

# --- SCHEMAS FOR WAREHOUSE ---
class WarehouseCreate(BaseModel):
    warehouse_name: str
    location: str

class WarehouseDetailResponse(WarehouseCreate):
    id: int
    # Lồng ghép danh sách kiện hàng
    packages: List[PackageDetail] = []
    model_config = ConfigDict(from_attributes=True)

# --- SCHEMAS FOR WAYBILL ---
class WaybillResponse(BaseModel):
    id: int
    tracking_number: str
    shipping_status: str
    package_id: int
    model_config = ConfigDict(from_attributes=True)