from fastapi import APIRouter
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.sessions import router as sessions_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(sessions_router)
