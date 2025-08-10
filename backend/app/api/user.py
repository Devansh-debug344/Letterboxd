from fastapi import APIRouter , Depends , HTTPException , status
from app.schemas.user import CreateUser , UserOut , UserProfile , UserUpdate
from sqlalchemy.orm import Session
from app.db.session import get_db 
from app.crud.user import create_user , get_user_by_email , get_user_by_username , get_user , get_user_profile , update_user
from app.auth.oauth import get_current_user
from app.models.user import User
from typing import List
router = APIRouter(
    prefix="/user",
    tags=['Users']
)

@router.post("/" , response_model=CreateUser)
def create_users(user_details : CreateUser , db : Session = Depends(get_db)):
    if get_user_by_username(username=user_details.username , db=db):       
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="User with same username already existed")
    if get_user_by_email(email = user_details.email , db=db):
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED , detail="User already existed")
    return create_user(user = user_details , db = db)

@router.get("/" , response_model=List[UserOut])
def get_users(db : Session = Depends(get_db)):
    return get_user(db=db)

@router.get('/profile' , response_model=UserProfile)
def get_profile(db: Session = Depends(get_db) , current_user : User = Depends(get_current_user)):
    return get_user_profile( id = current_user.id , db = db )

@router.patch('/profile' , response_model=UserUpdate)
def handle_update_user(user_details : UserUpdate , db : Session = Depends(get_db) , current_user : User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")

    updated_user = update_user(update_user = user_details , user  = user, db = db)
    
    return updated_user