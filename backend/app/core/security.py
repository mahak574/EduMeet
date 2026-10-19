import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from jose import jwt, JWTError
from app.config import settings


# ==============================================================================
# OTP Cryptography (HMAC-SHA256 with Server Secret)
# ==============================================================================
def generate_numeric_otp(length: int = 6) -> str:
    """Generates a cryptographically secure numeric OTP."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def compute_otp_hmac(email: str, code: str) -> str:
    """
    Computes HMAC-SHA256 digest using server secret.
    Standardized payload: lowercase trimmed email + ':' + code
    """
    normalized_email = email.lower().strip()
    payload = f"{normalized_email}:{code.strip()}".encode("utf-8")
    return hmac.new(
        settings.OTP_HMAC_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()


def verify_otp_hmac(email: str, code: str, expected_hmac: str) -> bool:
    """Constant-time verification of OTP against stored HMAC digest."""
    actual_hmac = compute_otp_hmac(email, code)
    return hmac.compare_digest(actual_hmac, expected_hmac)


# ==============================================================================
# JWT Access Tokens
# ==============================================================================
def create_access_token(
    user_id: str,
    role: str = "student",
    is_verified_student: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    jti = secrets.token_urlsafe(16)
    to_encode: Dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "is_verified": is_verified_student,
        "iat": now,
        "exp": expire,
        "jti": jti,
        "type": "access",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ==============================================================================
# Refresh Token Cryptography & Family Hashing
# ==============================================================================
def generate_refresh_token() -> Tuple[str, str]:
    """
    Generates a raw refresh token to send to client in httpOnly cookie,
    and returns (raw_token, sha256_hash_to_store_in_redis).
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, token_hash


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
