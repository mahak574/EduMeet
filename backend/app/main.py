import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.core.rate_limit import limiter
from app.database import close_db, init_db
from app.routers.api_v1 import api_v1_router
from app.schemas.common import APIError, APIResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("edumeet")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting EduMeet backend application [%s]...", settings.APP_ENV)
    await init_db()
    try:
        from app.services.question_bank import seed_canonical_question_bank
        await seed_canonical_question_bank()
    except Exception as exc:
        logger.warning("Could not auto-seed question bank during startup: %s", exc)
    yield
    logger.info("Shutting down EduMeet backend application...")
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    description="Global peer-to-peer complementary learning network backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach SlowAPI limiter
app.state.limiter = limiter

# CORS Configuration
origins = [
    settings.APP_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate Limit Exception Handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=APIResponse(
            success=False,
            error=APIError(
                code="RATE_LIMIT_EXCEEDED",
                message="Too many requests. Please slow down and try again later.",
                details={"retry_after": exc.detail},
            ),
        ).model_dump(),
    )


# Standard HTTP Exception Handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIResponse(
            success=False,
            error=APIError(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred. Please try again.",
            ),
        ).model_dump(),
    )


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


# Include API v1 Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
