from fastapi import APIRouter , Depends , HTTPException , status , Query
from app.schemas.user import CreateUser , UserOut , UserProfile , UserUpdate
from sqlalchemy.orm import Session
from app.db.session import get_db 
from app.crud.user import create_user , get_user_by_email , get_user_by_username , get_user , get_user_profile , update_user , get_user_by_id, get_user_stats, get_public_reviews_by_user
from app.auth.oauth import get_current_user
from app.models.user import User
from typing import List
from app.schemas.user import UserStats , UserOut
from app.schemas.review import ReviewOut
from app.crud.review import to_review_out
router = APIRouter(
    prefix="/user",
    tags=['Users']
)

@router.post("/" , response_model=UserOut)
def create_users(user_details : CreateUser , db : Session = Depends(get_db)):
    if get_user_by_username(user_details.username , db):       
        raise HTTPException(status_code=status.HTTP_409_CONFLICT , detail="User with same username already existed. Try another username.")
    if get_user_by_email(user_details.email , db):
         raise HTTPException(status_code=status.HTTP_409_CONFLICT , detail="User already existed")
    return create_user(user_details , db)

# @router.get("/" , response_model=List[UserOut])
# def get_users(db : Session = Depends(get_db)):
#     return get_user(db=db)

@router.get('/profile' , response_model=UserProfile)
def get_profile(db: Session = Depends(get_db) , current_user : User = Depends(get_current_user)):
    return get_user_profile(current_user.id , db )

@router.patch('/profile' , response_model=UserUpdate)
def handle_update_user(user_details : UserUpdate , db : Session = Depends(get_db) , current_user : User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")

    updated_user = update_user(user_details , user, db)
    
    return updated_user


@router.get("/{user_id}/stats", response_model=UserStats , status_code=status.HTTP_200_OK)
def handle_user_stats(user_id: int, db: Session = Depends(get_db)):
    if not get_user_by_id(user_id, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return get_user_stats(user_id, db)


@router.get("/{user_id}/reviews", response_model=List[ReviewOut] , status_code=status.HTTP_200_OK)
def handle_user_reviews(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    if not get_user_by_id(user_id, db):
        raise HTTPException(status_code=404, detail="User not found")

    skip = (page - 1) * limit
    items = get_public_reviews_by_user(user_id, db, skip, limit)
    return [to_review_out(r) for r in items]