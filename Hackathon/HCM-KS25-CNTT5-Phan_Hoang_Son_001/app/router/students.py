from fastapi import APIRouter, status, HTTPException, Request, Depends
from app.schemas.response import APIResponse, api_response
from app.schemas.students import CreateStudent
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.servies.students import *

router = APIRouter( tags=["Students"])



@router.get("/", status_code=status.HTTP_200_OK, response_model=APIResponse, tags=["Health"])
def get_health(request: Request):
    return api_response(request, statusCode=200, message="API đang chạy")

@router.get("/students", status_code=status.HTTP_200_OK, response_model=APIResponse)
def get_all_students(request: Request, db: Session = Depends(get_db)):
    list_students = get_all(db)
    return api_response(request, statusCode=200, message="Lấy danh sách sinh viên thành công", data=list_students)

@router.get("/students/search", response_model= APIResponse, status_code= status.HTTP_200_OK)
def search_student(
    request: Request,
    db: Session = Depends(get_db), 
    class_name: str | None = None,
):
    list_students = get_by_class(db, class_name)
    if not list_students:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy sinh viên nào")
    return api_response(request, statusCode=200, message="Lấy danh sách sinh viên thành công", data=list_students) 

@router.get("/students/{student_id}", status_code= status.HTTP_200_OK, response_model=APIResponse)
def get_student(student_id: int, request: Request, db: Session = Depends(get_db)):
    student = get_by_id(db=db, student_id=student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy sinh viên")
    return api_response(request, statusCode=200, message="Thông tin sinh viên", data=student)

@router.post("/students", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def create_student(student_data: CreateStudent, request: Request, db: Session = Depends(get_db)):
    try:
        new_student = create(db, student_data=student_data.model_dump())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gặp lỗi khi thêm sinh viên"
        )
    return api_response(request, statusCode=201, message="Tạo sinh viên thành công", data= new_student )

@router.put("/student/{student_id}", status_code=status.HTTP_200_OK, response_model=APIResponse)
def updata_student(student_id: int, student_data: CreateStudent,request:Request, db: Session = Depends(get_db)):
    try:
        student = update(db, student_id, student_data=student_data.model_dump())
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gặp lỗi khi sửa thông tin sinh viên")
    return api_response(request, statusCode=200, message="Cập nhật thông tin thành công", data=student)

@router.delete("/students/{student_id}", status_code=status.HTTP_200_OK, response_model=APIResponse)
def del_student(student_id: int, request: Request, db: Session = Depends(get_db)):
    try: 
        del_student(student_id, db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gặp lỗi khi xóa"
        )
    return api_response(request, statusCode=200, message="Xóa thành công")