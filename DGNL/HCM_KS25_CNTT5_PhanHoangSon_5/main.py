from fastapi import FastAPI, Request, status
import models
from database import Base, engine
from starlette.exceptions import HTTPException as StarHTTPExc
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from http import HTTPStatus
from router import router


Base.metadata.create_all(engine)

app = FastAPI()

app.include_router(router=router)

@app.exception_handler(StarHTTPExc)
def customer_httpexc(request: Request, exc: StarHTTPExc):
    JSONResponse(
        status_code=exc.status_code,
        content={
            "statusCode": exc.status_code,
            "error": HTTPStatus(exc.status_code).phrase,
            "message": exc.detail,
            "data": None
        }
    )
    

@app.exception_handler(ResponseValidationError)
def customer_validationerror(request: Request, exc: ResponseValidationError):
    JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "statusCode": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "error": str(exc.errors()),
            "message": "Dữ liệu đầu vào không hợp lệ",
            "data": None
        }
    )