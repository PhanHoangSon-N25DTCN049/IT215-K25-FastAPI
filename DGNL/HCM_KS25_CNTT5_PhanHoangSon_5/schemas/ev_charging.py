from pydantic import BaseModel, Field
from typing import Any, List


class StationCreate(BaseModel):
    station_code: str = Field(min_length=4, max_length=10)
    price_per_kwh: int = Field(gt=0)
    station_type_id: int
    


class StationResponse(BaseModel):
    statusCode: int
    error: str | None = None
    message: str
    data: Any | None = None
    
def api_response(statusCode: int, message: str, data: Any = None, error: str = None):
    return {
        "statusCode": statusCode,
        "error": error,
        "message": message,
        "data": data
    }