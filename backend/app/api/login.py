from fastapi import APIRouter , Depends , HTTPException ,status , Request
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.login import Token , LogoutResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.utils import verify_password
from app.auth.oauth import create_access_token
from app.schemas.refresh_token import RefreshTokenRequest , TokenResponse
from app.services.refresh_token_service import create_refresh_token , rotate_refresh_token
from app.services.rate_limiter import rate_limiter
from app.crud.refresh_token import get_token_db , revoke_all_token, revoke_token_by_id , revoke_alltoken_by_id
from app.utils import hash_token
from app.auth.oauth import get_current_user
from app.services.auth_event import AuditService
from app.schemas.auth_event import AuthEventSchema
from app.crud.user import get_user_by_username
router = APIRouter(
    tags=['Authentication']
)

@router.post("/login" , response_model=TokenResponse)
def login(user_details : OAuth2PasswordRequestForm = Depends() , db : Session = Depends(get_db), request : Request = None):

    username = user_details.username

    key = f"login:{username}"

    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

  
    if rate_limiter.is_rate_limited(key , max_attempts=5 , window_seconds= 900):
        # remaining = rate_limiter.get_remaining_attempts(key)

        auth_event = AuthEventSchema(
            event_type="login",
            status="failed",
            user_id = None,
            reason="Rate limit exceeded",
            ip_address=ip_address,
            user_agent=user_agent
        )

        AuditService.log_event(auth_event , db)

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in 15 minutes."
        )
   

    user = get_user_by_username(username , db)

    if not user:

        auth_event = AuthEventSchema(
            event_type="login",
            status="failed",
            user_id=None,
            reason="User not found",
            ip_address=ip_address,
            user_agent=user_agent
                )
        AuditService.log_event(auth_event , db)

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")

    if not verify_password(user_details.password , user.password):

        auth_event = AuthEventSchema(
            event_type="login",
            status="failed",
            user_id=user.id,
            reason="Wrong password",
            ip_address=ip_address,
            user_agent=user_agent
             )
        AuditService.log_event(auth_event , db)

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="Wrong password")
    
    access_token = create_access_token({'user_id' : user.id})

    if not access_token:

        auth_event = AuthEventSchema(
                    event_type="login",
                    status="failed",
                    user_id=user.id,
                    reason="Access Token Not found",
                    ip_address=ip_address,
                    user_agent=user_agent
                     )
        AuditService.log_event(auth_event , db)        

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="Access token not found")

    auth_event = AuthEventSchema(
        event_type="login",
        status="success",
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    AuditService.log_event(auth_event , db)

    refresh_token , _ = create_refresh_token(user.id , db)

    rate_limiter.reset(key)
    

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db), req : Request = None):
    
    try:
        new_access_token, new_refresh_token , user_id = rotate_refresh_token(request.refresh_token, db)

        ip_address = req.client.host if req else None
        user_agent = req.headers.get("user-agent") if request else None


        auth_event = AuthEventSchema(
                    event_type="refresh",
                    status="success",
                    user_id=user_id,
                    reason="Refresh token",
                    ip_address=ip_address,
                    user_agent=user_agent
                )

        AuditService.log_event(auth_event , db)

        return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
      

@router.post("/logout" , response_model = LogoutResponse)
def logout_user(current_user: User = Depends(get_current_user) , db: Session = Depends(get_db) , request : Request = None):

    revoke_token_by_id(current_user.id , db)

    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None

    auth_event = AuthEventSchema(
        event_type="logout",
        status="success",
        user_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
        )
    
    AuditService.log_event(auth_event , db)


    return {"message": f"Logged out successfully"}

@router.post("/logout-all", response_model=LogoutResponse)
def logout_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db) , request : Request = None):
    """Logout from all devices"""
    
    
    revoke_alltoken_by_id(current_user.id , db)

    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    
    auth_event = AuthEventSchema(
        event_type="logout_all",
        status="success",
        user_id=current_user.id,
        ip_address=ip_address,
        user_agent=user_agent
        )

    AuditService.log_event(auth_event , db)
    
    return {"message": f"All sessions logged out"}