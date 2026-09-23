from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.otp_service import otp_service
from app.services.refresh_token_service import create_refresh_token
from app.services.rate_limiter import rate_limiter
from app.auth.oauth import create_access_token
from app.schemas.otp import SendOTPRequest, VerifyOTPRequest, OTPResponse
from app.schemas.refresh_token import TokenResponse
from app.crud.user import create_user, get_user_by_username
from app.schemas.user import CreateUser

router = APIRouter(tags=['OTP Authentication'])


@router.post("/otp/send", response_model=OTPResponse)
async def send_otp(request: SendOTPRequest, db: AsyncSession = Depends(get_db), req: Request = None):
    await rate_limiter.enforce(
        req,
        "otp:send",
        max_attempts=5,
        window_seconds=900,
        detail="Too many OTP requests from this device. Try again later.",
    )
    await rate_limiter.enforce_key(
        f"rl:otp:send:phone:{request.phone_number}",
        max_attempts=3,
        window_seconds=3600,
        detail="Too many OTP requests for this number. Try again later.",
    )
    result = await otp_service.send_otp(request.phone_number)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return OTPResponse(message=result["message"])


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(request: VerifyOTPRequest, db: AsyncSession = Depends(get_db), req: Request = None):
    await rate_limiter.enforce(
        req,
        "otp:verify",
        max_attempts=10,
        window_seconds=900,
        detail="Too many verification attempts from this device. Try again later.",
    )
    await rate_limiter.enforce_key(
        f"rl:otp:verify:phone:{request.phone_number}",
        max_attempts=5,
        window_seconds=900,
        detail="Too many verification attempts for this number. Try again later.",
    )
    result = await otp_service.verify_otp(request.phone_number, request.code)

    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"],
        )

    user = await get_user_by_username(request.phone_number, db)

    if not user:
        user_param = CreateUser(
            username=request.phone_number,
            email=f"{request.phone_number}@otp.local",
            password="otp_auth",
        )
        user = await create_user(user_param, db)

    access_token = create_access_token(data={'user_id': user.id})

    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token not found")

    refresh_token, _ = await create_refresh_token(user.id, db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }