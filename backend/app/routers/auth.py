import logging
import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from app.config import settings
from app.core.rate_limit import limiter
from app.core.security import decode_access_token
from app.core.turnstile import verify_turnstile_token
from app.models.consolidated import User
from app.schemas.auth import (
    AuthTokenResponse,
    GoogleAuthRequest,
    SendOTPRequest,
    UserResponse,
    VerifyOTPRequest,
)
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        age_confirmed=user.age_confirmed,
        country=user.country,
        timezone=user.timezone,
        languages=user.languages,
        subjects_studied=user.subjects_studied,
        is_verified_student=user.is_verified_student,
        is_mentor=user.is_mentor,
    )


def _set_refresh_cookie(response: Response, raw_refresh: str) -> None:
    response.set_cookie(
        key="edumeet_refresh",
        value=raw_refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


@router.post("/otp/send", response_model=APIResponse[dict])
@limiter.limit("5/10minutes")
async def send_otp(request: Request, payload: SendOTPRequest):
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Verify Turnstile CAPTCHA
    is_valid_turnstile = await verify_turnstile_token(payload.turnstile_token, client_ip)
    if not is_valid_turnstile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security verification (Turnstile) failed. Please try again.",
        )

    await AuthService.request_otp(payload.email, client_ip)
    return APIResponse(
        success=True,
        data={"message": f"Verification code sent to {payload.email}"},
    )


@router.post("/otp/verify", response_model=APIResponse[AuthTokenResponse])
@limiter.limit("10/10minutes")
async def verify_otp(request: Request, response: Response, payload: VerifyOTPRequest):
    user, access_token, raw_refresh = await AuthService.verify_otp(
        email=payload.email,
        code=payload.code,
    )

    # Set httpOnly Secure SameSite cookie with refresh token
    _set_refresh_cookie(response, raw_refresh)

    return APIResponse(
        success=True,
        data=AuthTokenResponse(
            access_token=access_token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=_build_user_response(user),
        ),
    )


@router.post("/refresh", response_model=APIResponse[AuthTokenResponse])
@limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    response: Response,
    edumeet_refresh: str = Cookie(None),
):
    if not edumeet_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token cookie.",
        )

    user, new_access_token, new_raw_refresh = await AuthService.rotate_refresh_token(edumeet_refresh)
    _set_refresh_cookie(response, new_raw_refresh)

    return APIResponse(
        success=True,
        data=AuthTokenResponse(
            access_token=new_access_token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=_build_user_response(user),
        ),
    )


@router.post("/logout", response_model=APIResponse[dict])
async def logout(
    request: Request,
    response: Response,
    edumeet_refresh: str = Cookie(None),
):
    # Extract access token JTI if Bearer is provided
    auth_header = request.headers.get("Authorization")
    jti = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        if payload:
            jti = payload.get("jti")

    await AuthService.logout(raw_refresh=edumeet_refresh, access_token_jti=jti)
    # Clear cookie
    response.delete_cookie(
        key="edumeet_refresh",
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )
    return APIResponse(success=True, data={"message": "Logged out successfully."})


@router.get("/config")
async def get_auth_config():
    """
    Returns public OAuth and security configuration for frontend initialization.
    """
    return APIResponse(
        success=True,
        data={
            "google_client_id": settings.GOOGLE_CLIENT_ID,
            "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
        },
    )


async def verify_google_id_token(id_token: str) -> dict:
    """
    Verifies a Google OAuth2 ID token using google-auth verify_oauth2_token with required audience.
    Requires verified email and rejects mock tokens in non-development environments with 404.
    """
    # Gate mock tokens strictly to APP_ENV == "development"; return 404 otherwise
    if id_token.startswith("mock_") or id_token == "mock_google_id_token_demo":
        if settings.APP_ENV != "development":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not Found",
            )
        return {
            "email": "demo_student@example.com",
            "name": "Alex Rivera",
            "picture": None,
        }

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication is not configured.",
        )

    id_info = None
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        id_info = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            audience=settings.GOOGLE_CLIENT_ID,
        )
    except (ImportError, ModuleNotFoundError):
        # Fallback to Google's official tokeninfo endpoint if google-auth is not installed in current environment
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"id_token": id_token},
                )
                if resp.status_code == 200:
                    token_data = resp.json()
                    # Validate audience
                    if token_data.get("aud") == settings.GOOGLE_CLIENT_ID:
                        id_info = token_data
                    else:
                        logger.warning("Google token audience mismatch.")
        except Exception as net_exc:
            logger.warning(f"Google tokeninfo validation network error: {net_exc}")
    except Exception as exc:
        logger.warning(f"Google ID token verification failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google authentication token. Please sign in again.",
        )

    if not id_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Google authentication token. Please sign in again.",
        )

    email_verified = id_info.get("email_verified")
    if email_verified is not True and str(email_verified).lower() != "true":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your Google account email address must be verified.",
        )

    email = id_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your Google account did not supply an email address.",
        )

    return {
        "email": email.strip().lower(),
        "name": id_info.get("name") or email.split("@")[0],
        "picture": id_info.get("picture"),
    }


@router.post("/google", response_model=APIResponse[AuthTokenResponse])
async def google_auth(response: Response, payload: GoogleAuthRequest):
    """
    Authenticates a user using their genuine Google ID token.
    Extracts the user's authentic Google email and full name, provisions an account if first-time,
    and returns session access tokens. Never sets age_confirmed=True automatically.
    """
    profile = await verify_google_id_token(payload.id_token)
    email = profile["email"]
    full_name = profile["name"]

    user = await User.find_one(User.email == email)
    if not user:
        user = User(
            email=email,
            full_name=full_name,
            age_confirmed=False,
            country="US",
            timezone="UTC",
            role="student",
            subjects_studied=[],
        )
        await user.insert()
    else:
        # Update name if user previously had placeholder name
        if full_name and (not user.full_name or user.full_name in ("Student", "Alex Rivera")):
            user.full_name = full_name
            await user.save()

    from app.core.security import create_access_token, generate_refresh_token
    access_token = create_access_token(str(user.id), user.role, user.is_verified_student)
    raw_refresh, refresh_hash = generate_refresh_token()
    await AuthService._store_refresh_token(str(user.id), refresh_hash)
    _set_refresh_cookie(response, raw_refresh)

    return APIResponse(
        success=True,
        data=AuthTokenResponse(
            access_token=access_token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=_build_user_response(user),
        ),
    )


@router.post("/demo-login", response_model=APIResponse[AuthTokenResponse])
async def demo_login(response: Response):
    """
    1-click instant login for testing in development only. Returns 404 in non-development.
    """
    if settings.APP_ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        )

    email = "demo_student@example.com"
    user = await User.find_one(User.email == email)
    if not user:
        user = User(
            email=email,
            full_name="Alex Rivera",
            age_confirmed=True,
            country="US",
            timezone="UTC",
            role="student",
            subjects_studied=["python", "maths"],
        )
        await user.insert()

    from app.core.security import create_access_token, generate_refresh_token
    access_token = create_access_token(str(user.id), user.role, user.is_verified_student)
    raw_refresh, refresh_hash = generate_refresh_token()
    await AuthService._store_refresh_token(str(user.id), refresh_hash)
    _set_refresh_cookie(response, raw_refresh)

    return APIResponse(
        success=True,
        data=AuthTokenResponse(
            access_token=access_token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=_build_user_response(user),
        ),
    )
