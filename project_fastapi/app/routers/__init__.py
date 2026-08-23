from fastapi import APIRouter
from .auth import auth_router
from .users import user_router
from .projects import project_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(project_router)
