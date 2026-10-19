import os
import sys
from pathlib import Path

# 1. Resolve paths and ensure backend and its virtualenv packages are in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Automatically detect and include venv site-packages if running from an external Python/IDE
for venv_candidate in [
    backend_dir / ".venv" / "Lib" / "site-packages",
    backend_dir / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
]:
    if venv_candidate.exists() and str(venv_candidate) not in sys.path:
        sys.path.insert(0, str(venv_candidate))

# 2. Defend against broken host pyOpenSSL/service_identity (e.g. Anaconda version mismatches)
try:
    import OpenSSL
    _ = OpenSSL.crypto.X509Extension
except Exception:
    sys.modules["service_identity"] = None
    sys.modules["OpenSSL"] = None
    sys.modules["OpenSSL.crypto"] = None
    sys.modules["OpenSSL.SSL"] = None

# 3. Set environment variables BEFORE importing application settings or models
os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "test_secret_key_minimum_32_characters_long_12345"
os.environ["OTP_HMAC_SECRET"] = "test_otp_hmac_secret_minimum_32_characters_long"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017/edumeet_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

import pytest
import pytest_asyncio
from unittest.mock import MagicMock

# 4. Import models
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

ALL_DOCUMENT_MODELS = [
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
]

# 5. Optional mongomock_motor loader
try:
    from mongomock_motor import AsyncMongoMockClient  # type: ignore
    from beanie import init_beanie
    HAS_MONGOMOCK = True
except ImportError:
    HAS_MONGOMOCK = False


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    """
    Initializes an in-memory mock MongoDB for Beanie document models.
    Falls back to mocking DocumentSettings if mongomock_motor is not installed.
    """
    if HAS_MONGOMOCK:
        client = AsyncMongoMockClient()
        db = client.get_database("test_edumeet")
        await init_beanie(
            database=db,
            document_models=ALL_DOCUMENT_MODELS,
        )
        yield
        client.close()
    else:
        # Fallback for lightweight testing without mongomock installed
        for model in ALL_DOCUMENT_MODELS:
            if getattr(model, "_document_settings", None) is None:
                mock_settings = MagicMock()
                mock_settings.motor_collection = MagicMock()
                model._document_settings = mock_settings
        yield
