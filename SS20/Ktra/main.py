from fastapi import FastAPI, status, HTTPException, Depends, Request
from app.database import get_db, engine, Base
from app.models.models import *
from sqlalchemy.orm import Session
from app.schemas.schemas import *


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/employees", status_code=status.HTTP_200_OK, response_model=EmployeesResponse)
def get_employees(request: Request, db: Session = Depends(get_db)):
    list_employees = db.query(EmployeesModel).all()
    return api_response(
        request=request,
        statusCode=200,
        message="Lấy danh sách nhân viên thành công!",
        data=list_employees
    )
    

@app.post("/employees", status_code=status.HTTP_201_CREATED, response_model=EmployeesResponse)
def create_employees(request: Request, employees_data: CreateEmployees ,db: Session = Depends(get_db)):
    try:
        employees_new = employees_data.model_dump()
        if not db.query(DepartmentsModel).filter(DepartmentsModel.id == employees_new["department_id"]).first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Phòng ban không tồn tại"
            )
        
        if db.query(EmployeesModel).filter(EmployeesModel.employee_code == employees_new["employee_code"]).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã nhân viên đã tồn tại"
            )
        
        employees = EmployeesModel(**employees_new)
        db.add(employees)
        db.commit()
        db.refresh(employees)
    except Exception:
        HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gặp lỗi khi thêm nhân viên"
        )
    return api_response(
        request=request,
        statusCode=201,
        message="Thêm nhân viên thành công",
        data=employees
    )
    