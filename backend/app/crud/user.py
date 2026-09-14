from app.schemas.user import CreateUser , UserUpdate
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db
from app.models.user import User
from app.utils import hash_password
from sqlalchemy import func
from app.models.watched import Watched
from app.models.review import Review
from app.models.watchlist import WatchList

def create_user(user : CreateUser , db : Session):
    hashed_password = hash_password(user.password)
    user.password = hashed_password

    user = User(
        username = user.username,
        email = user.email,
        password = user.password
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def update_user(update_user : UserUpdate , user : User ,  db : Session):
    for key , value in update_user.model_dump(exclude_unset=True).items():
        setattr(user , key , value)
    db.commit()
    db.refresh(user)
    return user
   

def get_user(db : Session):
    return db.query(User).all()

def get_user_by_id(user_id : int , db : Session):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(username : str , db : Session):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(email : str , db : Session):
    return db.query(User).filter(User.email == email).first()

def get_user_profile(id : int , db : Session):
   return db.query(User).filter(User.id == id).first()


def get_user_by_id(user_id: int, db: Session) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_stats(user_id: int, db: Session) -> dict:
    watched_count = db.query(func.count(Watched.id)).filter(Watched.user_id == user_id).scalar()
    
    review_count = db.query(func.count(Review.id)).filter(Review.user_id == user_id).scalar()
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.user_id == user_id).scalar()
    WatchList_count = db.query(func.count(WatchList.id)).filter(WatchList.user_id == user_id).scalar()

    return {
        "user_id": user_id,
        "watched": watched_count or 0,
        "reviews": review_count or 0,
        "WatchList": WatchList_count or 0,
        "avg_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
    }


def get_public_reviews_by_user(user_id: int, db: Session, skip: int, limit: int):
    return (
        db.query(Review)
        .filter(Review.user_id == user_id)
        .order_by(Review.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )