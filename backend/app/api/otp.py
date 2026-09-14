from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.services.otp_service import otp_service
from app.services.refresh_token_service import create_refresh_token
from app.auth.oauth import create_access_token
from app.schemas.otp import SendOTPRequest, VerifyOTPRequest , OTPResponse
from app.schemas.refresh_token import TokenResponse
from pydantic import BaseModel
from app.crud.user import create_user , get_user_by_username
from app.schemas.user import CreateUser
router = APIRouter(tags=['OTP Authentication'])



@router.post("/otp/send", response_model=OTPResponse)
def send_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """Send OTP to phone number via Twilio"""
    result = otp_service.send_otp(request.phone_number)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return OTPResponse(message=result["message"])

@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP and login/signup user"""
    
    # Verify the OTP from Redis
    result = otp_service.verify_otp(request.phone_number, request.code)
    
    if not result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )
    
    # Get or create user with this phone

    user = get_user_by_username(request.phone_number , db)
    
    if not user:
        # New user via OTP (signup)
        user_param = CreateUser(
            username=request.phone_number,
            email=f"{request.phone_number}@otp.local",
            password="otp_auth"

        )

        user = create_user(user_param , db)
    
    
    # Create tokens
    access_token = create_access_token(data={'user_id': user.id})

    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="Access token not found")

    refresh_token, _ = create_refresh_token(user.id, db)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }