from fastapi import FastAPI, status, Request
from app.router.students import router
from app.schemas.response import APIResponse, api_response
from app.exceptions.exception import customer_exception

app = FastAPI()

app.include_router(router=router)

customer_exception(app=app)
