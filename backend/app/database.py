import logging
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as aioredis
from app.config import settings
from app.models.consolidated import (
    User,
    OTPChallenge,
    SkillProfile,
    SkillSnapshot,
    Question,
    QuizAttempt,
    Match,
    Availability,
    Session,
    Message,
    PeerQuiz,
    MistakeEntry,
    ReviewSchedule,
    Badge,
    Report,
    Block,
    PushSubscription,
    SessionNotes,
    InstantHelpRequest,
    TelemetryEvent,
)

logger = logging.getLogger(__name__)

motor_client: AsyncIOMotorClient = None
redis_client: aioredis.Redis = None


async def init_db() -> None:
    global motor_client, redis_client
    logger.info("Initializing MongoDB connection: %s", settings.MONGODB_URL)
    motor_client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Initialize Beanie with all Document models
    await init_beanie(
        database=motor_client.get_default_database(),
        document_models=[
            User,
            OTPChallenge,
            SkillProfile,
            SkillSnapshot,
            Question,
            QuizAttempt,
            Match,
            Availability,
            Session,
            Message,
            PeerQuiz,
            MistakeEntry,
            ReviewSchedule,
            Badge,
            Report,
            Block,
            PushSubscription,
            SessionNotes,
            InstantHelpRequest,
            TelemetryEvent,
        ],
    )
    logger.info("Beanie ODM successfully initialized with all collections.")

    logger.info("Initializing Redis connection: %s", settings.REDIS_URL)
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=2.0,
        )
        await redis_client.ping()
        logger.info("Redis connected successfully.")
    except Exception as exc:
        if settings.APP_ENV in {"development", "test"}:
            logger.warning(
                "Redis connection to %s failed (%s). Falling back to in-memory FakeRedis for local development. "
                "To use real Redis, run 'docker compose up redis -d' in another terminal.",
                settings.REDIS_URL,
                exc,
            )
            try:
                import fakeredis.aioredis
                redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
                logger.info("In-memory FakeRedis initialized successfully.")
            except ImportError:
                raise exc
        else:
            raise exc


async def close_db() -> None:
    global motor_client, redis_client
    if motor_client:
        motor_client.close()
        logger.info("MongoDB connection closed.")
    if redis_client:
        await redis_client.aclose()
        logger.info("Redis connection closed.")


def get_redis() -> any:
    return redis_client
