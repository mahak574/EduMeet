from fastapi import APIRouter
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.sessions import router as sessions_router
from app.routers.quizzes import router as quizzes_router
from app.routers.skills import router as skills_router
from app.routers.matching import router as matching_router
from app.routers.peer_quizzes import router as peer_quizzes_router
from app.routers.reviews import router as reviews_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(quizzes_router)
api_v1_router.include_router(skills_router)
api_v1_router.include_router(matching_router)
api_v1_router.include_router(peer_quizzes_router)
api_v1_router.include_router(reviews_router)
