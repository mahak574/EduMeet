import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from fastapi import HTTPException, status
from app.config import settings
from app.core.security import (
    compute_otp_hmac,
    create_access_token,
    generate_numeric_otp,
    generate_refresh_token,
    hash_refresh_token,
    verify_otp_hmac,
)
from app.database import get_redis
from app.models.consolidated import OTPChallenge, User, SkillProfile
from app.services.email_service import get_email_provider

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    async def request_otp(email: str, client_ip: str) -> None:
        normalized_email = email.lower().strip()
        redis = get_redis()

        # 1. Enforce rate limits via Redis
        email_key = f"rl:otp:email:{normalized_email}"
        ip_key = f"rl:otp:ip:{client_ip}"

        email_reqs = await redis.incr(email_key)
        if email_reqs == 1:
            await redis.expire(email_key, 3600)  # 1 hour window
        if email_reqs > 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests for this email. Please wait an hour.",
            )

        ip_reqs = await redis.incr(ip_key)
        if ip_reqs == 1:
            await redis.expire(ip_key, 600)  # 10 minute window
        if ip_reqs > 10:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests from this IP address. Please wait a few minutes.",
            )

        # 2. Invalidate all older challenges for this email
        await OTPChallenge.find(
            OTPChallenge.email == normalized_email,
            OTPChallenge.is_used == False,
        ).update({"$set": {"is_used": True}})

        # 3. Generate new 6-digit OTP & HMAC
        code = generate_numeric_otp(6)
        hashed_otp = compute_otp_hmac(normalized_email, code)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        challenge = OTPChallenge(
            email=normalized_email,
            hashed_otp=hashed_otp,
            expires_at=expires_at,
        )
        await challenge.insert()

        # 4. Dispatch via EmailProvider
        email_provider = get_email_provider()
        sent = await email_provider.send_otp(normalized_email, code)
        if not sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to dispatch verification email. Please try again later.",
            )

    @staticmethod
    async def verify_otp(email: str, code: str) -> Tuple[User, str, str]:
        """
        Verifies OTP and returns (user, access_token, refresh_token).
        Creates user if doesn't exist yet (signup flow requires age confirmation afterwards).
        """
        normalized_email = email.lower().strip()
        now = datetime.now(timezone.utc)

        # Find latest active challenge
        challenge = await OTPChallenge.find(
            OTPChallenge.email == normalized_email,
            OTPChallenge.is_used == False,
            OTPChallenge.expires_at > now,
        ).sort(-OTPChallenge.created_at).first_or_none()

        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code. Please request a new one.",
            )

        # Check attempts
        if challenge.attempts >= challenge.max_attempts:
            challenge.is_used = True
            await challenge.save()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Please request a new code.",
            )

        is_valid = verify_otp_hmac(normalized_email, code, challenge.hashed_otp)
        if not is_valid:
            challenge.attempts += 1
            if challenge.attempts >= challenge.max_attempts:
                challenge.is_used = True
            await challenge.save()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect verification code.",
            )

        # Mark challenge as used
        challenge.is_used = True
        await challenge.save()

        # Fetch or create user record
        user = await User.find_one(User.email == normalized_email)
        if not user:
            # Create user placeholder; age confirmation & profile completion done next
            user = User(
                email=normalized_email,
                full_name="",
                age_confirmed=False,
                country="US",
                timezone="UTC",
                role="student",
            )
            await user.insert()
            # Also create corresponding skill profile
            skill_profile = SkillProfile(user_id=user.id)
            await skill_profile.insert()

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated or suspended.",
            )

        # Generate tokens
        access_token = create_access_token(
            user_id=str(user.id),
            role=user.role,
            is_verified_student=user.is_verified_student,
        )
        raw_refresh, refresh_hash = generate_refresh_token()
        await AuthService._store_refresh_token(str(user.id), refresh_hash)

        return user, access_token, raw_refresh

    @staticmethod
    async def rotate_refresh_token(raw_refresh: str) -> Tuple[User, str, str]:
        """
        Rotates refresh token with reuse detection.
        If an old already-rotated token is re-presented, revoke all sessions (family revocation).
        """
        redis = get_redis()
        token_hash = hash_refresh_token(raw_refresh)
        key = f"refresh:{token_hash}"

        user_id = await redis.get(key)
        if not user_id:
            # Check if this token was previously revoked / used (reuse alert)
            was_used = await redis.get(f"revoked_refresh:{token_hash}")
            if was_used:
                # Potential token theft! Revoke all tokens for that user
                logger.warning("Token reuse detected for user %s! Revoking all sessions.", was_used)
                await AuthService.revoke_all_user_sessions(was_used)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token. Please sign in again.",
            )

        user = await User.get(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or account deactivated.",
            )

        # 1. Delete current refresh token & mark as used
        await redis.delete(key)
        await redis.setex(f"revoked_refresh:{token_hash}", 86400, user_id)  # Remember for 24h for reuse detection

        # 2. Issue new pair
        new_access_token = create_access_token(
            user_id=str(user.id),
            role=user.role,
            is_verified_student=user.is_verified_student,
        )
        new_raw_refresh, new_refresh_hash = generate_refresh_token()
        await AuthService._store_refresh_token(str(user.id), new_refresh_hash)

        return user, new_access_token, new_raw_refresh

    @staticmethod
    async def logout(raw_refresh: Optional[str], access_token_jti: Optional[str]) -> None:
        redis: any = get_redis()
        if raw_refresh:
            token_hash = hash_refresh_token(raw_refresh)
            user_id = await redis.get(f"refresh:{token_hash}")
            if user_id:
                await redis.delete(f"refresh:{token_hash}")
                await redis.srem(f"user_tokens:{user_id}", token_hash)  # type: ignore

        if access_token_jti:
            # Denylist access token until its expiration (15 mins)
            await redis.setex(f"jti_denylist:{access_token_jti}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1")

    @staticmethod
    async def _store_refresh_token(user_id: str, token_hash: str) -> None:
        redis: any = get_redis()
        expire_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        # Store token -> user mapping
        await redis.setex(f"refresh:{token_hash}", expire_seconds, user_id)
        # Add to user's set of active refresh tokens
        await redis.sadd(f"user_tokens:{user_id}", token_hash)  # type: ignore
        await redis.expire(f"user_tokens:{user_id}", expire_seconds)

    @staticmethod
    async def revoke_all_user_sessions(user_id: str) -> None:
        redis: any = get_redis()
        active_hashes = await redis.smembers(f"user_tokens:{user_id}")  # type: ignore
        if active_hashes:
            keys = [f"refresh:{h}" for h in active_hashes]
            await redis.delete(*keys)
        await redis.delete(f"user_tokens:{user_id}")
