from app.database import get_db
from fastapi import APIRouter, status, HTTPException, Request, Depends
from app.schemas.response import APIResponse, api_response
from app.services.student import *
from app.schemas.student import Student
router = APIRouter(tags=["students"])

@router.get("/students", status_code=status.HTTP_200_OK, response_model=APIResponse)
def get_students_router(request: Request, db: Session = Depends(get_db)):
    list_student = get_all(db)
    return api_response(request, statusCode=200, message="Lấy danh sách sinh viên thành công", data=list_student)

@router.get("/students/{student_id}", status_code=status.HTTP_200_OK, response_model=APIResponse)
def get_student_router(request: Request, student_id: int, db: Session = Depends(get_db)):
    student = get_by_id(student_id=student_id, db=db)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found!"
        )
    return api_response(request, statusCode=200, message="Tìm thấy sinh viên", data=student)


@router.post("/students",status_code=status.HTTP_201_CREATED, response_model= APIResponse)
def create_student_router(student_data: Student, request: Request, db: Session = Depends(get_db)):
    try:
        new_student = create(student_data.model_dump(), db)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gặp lỗi khi thêm sinh viên"
        )
    return api_response(request, statusCode=201, message="Tạo sinh viên mới thành công", data= new_student)


@router.put("/students/{student_id}", status_code=status.HTTP_200_OK, response_model=APIResponse)
def update_student_router(student_id: int ,student_data: Student, request: Request, db: Session = Depends(get_db)):
    db_student = get_by_id(student_id, db)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Student not found!")
    try:
        student = update(student_data=student_data.model_dump(), db_student=db_student, db=db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi cập nhật sinh viên"
        )
    return api_response(request, statusCode=200, message="Cập nhật thông tin sinh viên thành công", data=student)
        
@router.delete("/students/{student_id}", status_code=status.HTTP_200_OK, response_model=APIResponse)
def del_student_router(student_id:int, request: Request, db: Session = Depends(get_db)):
    student_del = get_by_id(student_id=student_id, db=db)
    if not student_del:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Student not found!")  
    try:
        del_student(db_student=student_del, db=db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gặp lỗi khi xóa sinh viên"
        )
    return api_response(request, statusCode=200, message="Xóa sinh viên thành công")