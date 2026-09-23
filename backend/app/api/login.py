from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.login import LogoutResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.login import DataToken
from app.utils import verify_password_async
from app.auth.oauth import create_access_token
from app.schemas.refresh_token import RefreshTokenRequest, TokenResponse
from app.services.refresh_token_service import create_refresh_token, rotate_refresh_token
from app.services.rate_limiter import rate_limiter
from app.crud.refresh_token import revoke_token_by_id, revoke_alltoken_by_id
from app.auth.oauth import get_current_user
from app.services.auth_event import AuditService
from app.schemas.auth_event import AuthEventSchema
from app.crud.user import get_user_by_username

router = APIRouter(
    tags=['Authentication']
)


@router.post("/login", response_model=TokenResponse)
async def login(
    user_details: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    username = user_details.username
    key = f"login:{username}"

    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    if await rate_limiter.is_rate_limited(rate_limiter.key("login", ip=ip_address or "unknown"), max_attempts=20, window_seconds=900):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts from this device. Try again in 15 minutes.",
        )

    if await rate_limiter.is_rate_limited(key, max_attempts=5, window_seconds=900):
        auth_event = AuthEventSchema(
            event_type="login",
            status="failed",
            user_id=None,
            reason="Rate limit exceeded",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await AuditService.log_event(auth_event, db)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in 15 minutes.",
        )

    user = await get_user_by_username(username, db)

    if not user:
        auth_event = AuthEventSchema(
            event_type="login",
            status="failed",
            user_id=None,
            reason="User not found",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await AuditService.log_event(auth_event, db)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not await verify_password_async(user_details.password, user.password):
        auth_event = AuthEventSchema(
            event_type="login",
            status="failed",
            user_id=user.id,
            reason="Wrong password",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await AuditService.log_event(auth_event, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")

    access_token = create_access_token({'user_id': user.id})

    if not access_token:
        auth_event = AuthEventSchema(
            event_type="login",
            status="failed",
            user_id=user.id,
            reason="Access Token Not found",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await AuditService.log_event(auth_event, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token not found")

    auth_event = AuthEventSchema(
        event_type="login",
        status="success",
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await AuditService.log_event(auth_event, db)

    refresh_token, _ = await create_refresh_token(user.id, db)

    await rate_limiter.reset(key)
    await rate_limiter.reset(rate_limiter.key("login", ip=ip_address or "unknown"))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    req: Request = None,
):
    await rate_limiter.enforce(
        req,
        "refresh",
        max_attempts=30,
        window_seconds=900,
        detail="Too many token refreshes. Please try again later.",
    )
    try:
        new_access_token, new_refresh_token, user_id = await rotate_refresh_token(request.refresh_token, db)

        ip_address = req.client.host if req else None
        user_agent = req.headers.get("user-agent") if req else None

        auth_event = AuthEventSchema(
            event_type="refresh",
            status="success",
            user_id=user_id,
            reason="Refresh token",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await AuditService.log_event(auth_event, db)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    current_user: DataToken = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    await rate_limiter.enforce(request, "logout", user_id=current_user.id, max_attempts=30, window_seconds=60)
    await revoke_token_by_id(current_user.id, db)

    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    auth_event = AuthEventSchema(
        event_type="logout",
        status="success",
        user_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await AuditService.log_event(auth_event, db)

    return {"message": "Logged out successfully"}


@router.post("/logout-all", response_model=LogoutResponse)
async def logout_all(
    current_user: DataToken = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    await rate_limiter.enforce(request, "logout", user_id=current_user.id, max_attempts=30, window_seconds=60)
    await revoke_alltoken_by_id(current_user.id, db)

    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    auth_event = AuthEventSchema(
        event_type="logout_all",
        status="success",
        user_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    await AuditService.log_event(auth_event, db)

    return {"message": "All sessions logged out"}