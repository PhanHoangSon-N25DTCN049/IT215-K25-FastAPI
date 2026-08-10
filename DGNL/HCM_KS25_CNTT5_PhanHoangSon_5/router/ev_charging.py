from fastapi import status, APIRouter, HTTPException, Depends
from database import get_db
from schemas.ev_charging import *
from models.ev_charging import *

from sqlalchemy.orm import Session


router = APIRouter(tags=["ev_charging_management"])

@router.post("/stations", status_code=status.HTTP_201_CREATED, response_model=StationResponse)
def post_stations(station_data:StationCreate, db: Session = Depends(get_db)):
    station_data = station_data.model_dump()
    if db.query(StationsModel).filter(StationsModel.station_code == station_data["station_code"]).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã Trạm sạc đã tồn tại"
        )
    
    
    new_station = StationsModel(**station_data)
    db.add(new_station)
    db.commit()
    db.refresh(new_station)
    return api_response(statusCode=201, message="Thêm mới trạm sạc thành công", data=new_station)
    
    

@router.get("/stations", status_code=status.HTTP_201_CREATED, response_model=StationResponse)
def get_stations(db: Session = Depends(get_db)):
    return api_response(
        statusCode=200,
        message="Lấy danh sách trạm sạc thành công",
        data= db.query(StationsModel).all()
    )
    