from fastapi import APIRouter
from src.routers.item import router as item_router
from src.routers.megamart import router as megamart_router

api_router = APIRouter(prefix="/api/v1")

# Gộp tất cả các sub-routers vào api_router
api_router.include_router(item_router)
api_router.include_router(megamart_router)
