from fastapi import FastAPI, HTTPException, status, Request
from pydantic import BaseModel, Field, field_validator
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Any
from datetime import datetime

flights_db = [
    {"id": 1, "flight_number": "VN-213", "destination": "Da Nang", "available_seats": 45, "status": "scheduled", "created_at": "2026-07-01T06:00:00Z"},
    {"id": 2, "flight_number": "VJ-122", "destination": "Phu Quoc", "available_seats": 12, "status": "scheduled", "created_at": "2026-07-01T07:30:00Z"}
]


app = FastAPI()
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
def Customer_HTTPException(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "status": "Fail",
            "message": str(exc.detail),
            "data": None,
            "error": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )
    


class CreateFlights(BaseModel):
    flight_number: str = Field(..., min_length=5, max_length=10)
    destination: str
    available_seats: int = Field(ge=1)
    
    @field_validator("flight_number", "destination")
    @classmethod
    def validate_space(cls, value:str):
        temp = value.strip()
        if temp:
            return temp
        raise ValueError("Không được để trống dữ liệu")
    
    

@app.get("/flights", status_code=status.HTTP_200_OK,response_model=ResponseAPI, tags=["Flights"])
def get_flights(
    status:str | None = None,
):
    if not status:
        flights_list = [f for f in flights_list if f["status"] == status]
    return api_response(status=200, message="Lấy danh sách chuyến bay thành công", data=flights_list)

@app.post("/flights", status_code=status.HTTP_201_CREATED, response_model=ResponseAPI, tags=["Flights"])
def create_flight(flight: CreateFlights):
    
    if any(f["flight_number"] == flight.flight_number for f in flights_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lỗi: Số hiệu chuyến bay này đã tồn tại trên hệ thống điều hành!"
        )
    
    new_flight = {
        "id": max((f["id"] for f in flights_db), default=0) + 1,
        "flight_number": flight.flight_number,
        "destination": flight.destination,
        "available_seats": flight.available_seats,
        "status":"scheduled",
        "created_at": datetime.now().isoformat()
    }
    
    flights_db.append(new_flight)
    return api_response(status=201, message="Khởi tạo chuyến bay mới thành công!", data=new_flight)


@app.delete("flights/{flight_id}", status_code=status.HTTP_200_OK, response_model=ResponseAPI, tags=["Flights"])
def del_flight(flight_id:int):
    flight = next((f for f in flights_db if f["id"] == flight_id), None)
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lỗi: Không tìm thấy mã chuyến bay yêu cầu để hủy!"
        )
    flights_db.remove(flight)
    return api_response(status=200, message="Hủy chuyến bay thành công!")