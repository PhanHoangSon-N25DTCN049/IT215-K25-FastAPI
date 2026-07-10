from fastapi import FastAPI
from app.exceptions.exception import setup_handler
from app.router.student import router

app = FastAPI()
setup_handler(app)
app.include_router(router)
