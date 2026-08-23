from fastapi import FastAPI, Depends, APIRouter, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List, Literal


from app.schemas import ApiResponse, api_response, UserData
from app.core import InvalidInputException
from app.db import get_db
from app.models import UserModel
from app.services import query_user_by_admin
from app.dependencies import allow_admin_only, get_current_user

user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.get("/me", status_code=200, response_model= ApiResponse[UserData])
def get_me(request: Request, user_data: UserModel = Depends(get_current_user)):
    return api_response(
        request,
        200,
        message="Lấy thông tin thành công",
        data=user_data
    )
    
@user_router.get("", status_code=200, dependencies=[Depends(allow_admin_only)], response_model=ApiResponse[List[UserData]])
def get_user_by_admin(request:Request,
             email: str | None = None,
             name: str | None = None,
             status: bool  | None = None,
             db: Session = Depends(get_db)):
    try:
        list_user = query_user_by_admin(db, name, email, status)
    except Exception:
        raise InvalidInputException()
    
    return api_response(
        request,
        200,
        "Danh sách user",
        list_user
    )