from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import Literal

# Dữ liệu mẫu
rooms = [
    {"id": 1, "code": "R101", "name": "Room 101", "capacity": 30, "status": "AVAILABLE"},
    {"id": 2, "code": "R102", "name": "Room 102", "capacity": 20, "status": "AVAILABLE"},
    {"id": 3, "code": "R103", "name": "Room 103", "capacity": 40, "status": "MAINTENANCE"}
]

room_bookings = [
    {
        "id": 1,
        "room_id": 1,
        "class_name": "Python Basic",
        "student_count": 25,
        "date": "2026-07-01",
        "slot": "MORNING"
    }
]

app = FastAPI()



class RequestRoom(BaseModel):
    code: str
    name: str
    capacity: int = Field(gt=0)
    status: Literal["AVAILABLE", "IN_USE", "MAINTENANCE"]

    @field_validator("name", "code")
    @classmethod
    def validate_string(cls, value: str, info):
        temp = value.strip()
        if not temp:
            raise ValueError(f"{info.field_name} không được bỏ trống")
        return temp


class RequestBooking(BaseModel):
    room_id: int
    class_name: str
    student_count: int = Field(gt=0)
    date: str
    slot: Literal["MORNING", "AFTERNOON", "EVENING"]

    @field_validator("class_name", "date")
    @classmethod
    def validate_string(cls, value: str, info):
        temp = value.strip()
        if not temp:
            raise ValueError(f"{info.field_name} không được bỏ trống")
        return temp

# ----------------- ROOMS API -----------------

@app.get("/rooms")
def get_rooms(
    keyword: str | None = None, 
    status_filter: Literal["AVAILABLE", "IN_USE", "MAINTENANCE"] | None = Query(default=None, alias="status"), 
    min_capacity: int | None = Query(default=None, gt=0)
):
    list_rooms = rooms
    
    if keyword:
        list_rooms = [r for r in list_rooms if keyword.lower() in r["name"].lower() or keyword.lower() in r["code"].lower()]
    
    if status_filter:
        list_rooms = [r for r in list_rooms if r["status"] == status_filter]
        
    if min_capacity:
        list_rooms = [r for r in list_rooms if r["capacity"] >= min_capacity]

    return {
        "status": "success",
        "message": "Danh sách phòng học tìm thấy",
        "data": list_rooms
    }


@app.get("/rooms/{room_id}")
def get_room_by_id(room_id: int):
    room = next((r for r in rooms if room_id == r["id"]), None)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    
    return {
        "status": "success",
        "message": "Thông tin phòng học",
        "data": room
    }


@app.post("/rooms")
def create_room(room: RequestRoom):
    if any(r["code"] == room.code for r in rooms):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mã phòng đã tồn tại")
    
    new_room = {
        "id": max((r["id"] for r in rooms), default=0) + 1,
        "code": room.code,
        "name": room.name,
        "capacity": room.capacity,
        "status": room.status
    }
    rooms.append(new_room)
    
    return {
        "status": "success",
        "message": "Thêm phòng học thành công",
        "data": new_room
    }


@app.put("/rooms/{room_id}")
def update_room(room_id: int, room: RequestRoom):
    room_update = next((r for r in rooms if room_id == r["id"]), None)
    if not room_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    
    if any(r["code"] == room.code and r["id"] != room_id for r in rooms):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mã phòng cập nhật đã tồn tại ở phòng khác")
    
    room_update.update(room.model_dump())
    
    return {
        "status": "success",
        "message": "Cập nhật thông tin phòng học thành công",
        "data": room_update
    }


@app.delete("/rooms/{room_id}")
def del_room(room_id: int):
    room = next((r for r in rooms if room_id == r["id"]), None)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    
    rooms.remove(room)
    
    return {
        "status": "success",
        "message": "Xóa phòng học thành công"
    }



@app.get("/room-bookings")
def get_room_bookings():
    return {
        "status": "success",
        "message": "Danh sách lịch đặt phòng",
        "data": room_bookings
    }


@app.post("/room-bookings")
def create_booking(booking: RequestBooking):
    # Kiểm tra phòng có tồn tại không
    room = next((r for r in rooms if r["id"] == booking.room_id), None)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phòng không tồn tại")
    
    # Kiểm tra trạng thái khả dụng
    if room["status"] != "AVAILABLE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phòng hiện không khả dụng để đặt")
        
    # Kiểm tra sức chứa
    if booking.student_count > room["capacity"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Số lượng học viên vượt quá sức chứa của phòng")
        
    is_conflict = any(
        b["room_id"] == booking.room_id and 
        b["date"] == booking.date and 
        b["slot"] == booking.slot 
        for b in room_bookings
    )
    
    if is_conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phòng đã được đặt trùng ngày và ca học này")
    
    # Thêm lịch mới
    new_booking = {
        "id": max((b["id"] for b in room_bookings), default=0) + 1,
        "room_id": booking.room_id,
        "class_name": booking.class_name,
        "student_count": booking.student_count,
        "date": booking.date,
        "slot": booking.slot
    }
    room_bookings.append(new_booking)
    
    return {
        "status": "success",
        "message": "Đặt lịch phòng thành công",
        "data": new_booking
    }