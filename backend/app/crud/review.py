from sqlalchemy.orm import Session
from fastapi import Depends , HTTPException ,status
from app.db.session import get_db
from app.models.review import Review
from app.schemas.review import ReviewCreate , ReviewUpdate

def create_review(user_id : int , movie_id : int , movie_review : ReviewCreate , db :  Session = Depends(get_db)):
    
    existing_review = db.query(Review).filter(
    Review.movie_id == movie_id,
    Review.user_id == user_id  # ⬅ Add this condition
    ).first()
    if existing_review:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="Review already created")

    review = Review(user_id=user_id, movie_id=movie_id, review = movie_review.review , likes = movie_review.likes)
    db.add(review)
    db.commit()
    db.refresh(review)

    return review

def update_review(user_id : int  , movie_update : ReviewUpdate , db :  Session = Depends(get_db)):
    review = db.query(Review).filter(Review.user_id == user_id).first()
    if not review:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Review not found")
    
    for key , value in movie_update.dict(exclude_unset=True).items():
        setattr(review , key , value)

    db.commit()
    db.refresh(review)
    
    return review