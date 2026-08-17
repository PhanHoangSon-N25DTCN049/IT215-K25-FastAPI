from fastapi import FastAPI
from app.models.devconnect import *
from app.database import Base, engine 
from app.router.devconnect_router import router
Base.metadata.create_all(engine)

app = FastAPI()

app.include_router(router=router)