from app.schemas.user import CreateUser , UserUpdate
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db
from app.models.user import User
from app.utils import hash_password
def create_user(user : CreateUser , db : Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    user.password = hashed_password

    user = User(**user.dict())
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def update_user(update_user : UserUpdate , user : User ,  db : Session = Depends(get_db)):
    for key , value in update_user.dict(exclude_unset=True).items():
        setattr(user , key , value)
    db.commit()
    db.refresh(user)
    return user
   

def get_user(db : Session = Depends(get_db)):
    return db.query(User).all()

def get_user_by_username(username : str , db : Session = Depends(get_db)):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(email : str , db : Session = Depends(get_db)):
    return db.query(User).filter(User.email == email).first()

def get_user_profile(id : int , db : Session = Depends(get_db)):
   return db.query(User).filter(User.id == id).first()