from fastapi import FastAPI, status, HTTPException, Depends, Request
from app.database import get_db, engine, Base
from app.models.models import *
from sqlalchemy.orm import Session
from app.schemas.schemas import *
from starlette.exceptions import HTTPException as StarHTTPExc
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError
from http import HTTPStatus


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.exception_handler(StarHTTPExc)
def customer_HTTPExc(request: Request, exc: StarHTTPExc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "statusCode": exc.status_code,
            "message": exc.detail,
            "data": None,
            "error": HTTPStatus(exc.status_code).phrase,
            "path": request.url.path
        }
    )
    
@app.exception_handler(ResponseValidationError)
def customer_responseValidation(request: Request, exc: ResponseValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "statusCode": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Lỗi dữ liệu đầu vào",
            "data": None,
            "error": str(exc.errors()),
            "path": request.url.path
        }
    )

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
            raise ValueError("Not Fount")
        
        if db.query(EmployeesModel).filter(EmployeesModel.employee_code == employees_new["employee_code"]).first():
            raise ValueError("Bad Request")
        
        employees = EmployeesModel(**employees_new)
        db.add(employees)
        db.commit()
        db.refresh(employees)
    except ValueError as e:
        error = str(e)
        if error == "Not Fount":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Phòng Ban Không Tồn Tại"
            )
        elif error == "Bad Request":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã nhân viên đã tồn tại"
            )
    return api_response(
        request=request,
        statusCode=201,
        message="Thêm nhân viên thành công",
        data=employees
    )

@app.post("/departments", status_code=status.HTTP_201_CREATED, response_model=DepartmentsResponse)
def create_employees(request: Request, departments_data: CreateDepartments,db: Session = Depends(get_db)):
    try:
        departments_new = departments_data.model_dump()
        if db.query(DepartmentsModel).filter(DepartmentsModel.department_code == departments_new["department_code"]).first():
            raise ValueError("Bad Request")
        
        departments = DepartmentsModel(**departments_new)
        db.add(departments)
        db.commit()
        db.refresh(departments)
    except ValueError as e:
        error = str(e)
        if error == "Bad Request":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã Phòng Ban Đã Tồn Tại"
            )
            
    return api_response(
        request=request,
        statusCode=201,
        message="Thêm phòng ban thành công",
        data=departments
    )
    