import socket
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

# SlowAPI Limiter configured with Redis backend or in-memory fallback
storage_uri = settings.REDIS_URL
if settings.APP_ENV in {"development", "test"}:
    try:
        s = socket.create_connection(("localhost", 6379), timeout=0.3)
        s.close()
    except OSError:
        storage_uri = "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=["100/minute"],
)
