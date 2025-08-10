from fastapi import APIRouter , Depends , HTTPException ,status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.login import Token
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.utils import verify_password
from app.auth.oauth import create_access_token
router = APIRouter(
    tags=['Authentication']
)

@router.post("/login" , response_model=Token)
def login(user_details : OAuth2PasswordRequestForm = Depends() , db : Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_details.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")
    password = verify_password(user_details.password , user.password)
    if not password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="Wrong password")
    response_token = create_access_token(data={'user_id' : user.id})
    
    return({"access_token" : response_token , "token_type" : "bearer"})