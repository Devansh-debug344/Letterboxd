from fastapi import APIRouter , Depends ,HTTPException , status
from app.schemas.review import ReviewCreate , ReviewDelete , ReviewOut , ReviewUpdate
from app.models.user import User
from app.models.movie import Movie
from app.models.review import Review
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.oauth import get_current_user
from app.crud.review import create_review , update_review
from typing import List
from fastapi import Query
from app.crud.watchlist import save_movie_db
from app.services.fetch_api import fetch_movies_from_api
router = APIRouter(
    prefix='/review',
    tags=['Reviews']
)

@router.post("/" , response_model=ReviewOut)
async def handle_create_review(review : ReviewCreate , current_user : User = Depends(get_current_user) , db :  Session = Depends(get_db)):
    print("🔔 Received POST to /review/")

    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")
     
    movie = db.query(Movie).filter(Movie.title == review.movie_name).first()

    if not movie:
        response = await fetch_movies_from_api(name = review.movie_name)
        if response.get("Response") == "False":
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found from OMDB")

        movie = save_movie_db(response = response , db=db)

    movie_review =  create_review( user_id = user.id , movie_id = movie.id , movie_review = review , db=db)

    return ReviewOut(
            movie_id=movie_review.movie_id,
            user_id = movie_review.user_id,
            movie_name=movie_review.movie.title,
            user_name=movie_review.user.username,
            review = movie_review.review,
            likes=movie_review.likes,
            updated_at=movie_review.updated_at
        )

@router.patch("/" , response_model=ReviewOut)
def handle_update_review(review_update : ReviewUpdate , current_user : User = Depends(get_current_user) , db :  Session = Depends(get_db)):
       
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")
     
    movie = db.query(Movie).filter(Movie.title == review_update.movie_name).first()

    if not movie:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Movie not found")
    
    update_movie =  update_review( user_id = user.id  , movie_update = review_update , db=db)

    return ReviewOut(
        movie_id=update_movie.movie_id,
        user_id=update_movie.user_id,
        movie_name=update_movie.movie.title,
        user_name=update_movie.user.username,
        review=update_movie.review,
        likes=update_movie.likes,
        updated_at = update_movie.updated_at
    )



@router.get('/', response_model=List[ReviewOut])
def handle_get_review(
    movie_name: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Review).filter(Review.user_id == current_user.id)

    if movie_name:
        movie = db.query(Movie).filter(Movie.title == movie_name).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        query = query.filter(Review.movie_id == movie.id)
    
    user_reviews = query.all()

    return [
        ReviewOut(
            movie_id=rev.movie_id,
            user_id=rev.user_id,
            movie_name=rev.movie.title,
            user_name=rev.user.username,
            review=rev.review,
            likes=rev.likes,
            updated_at=rev.updated_at
        )
        for rev in user_reviews
    ]



@router.delete('/')
def handle_delete_review(movie : ReviewDelete , db :  Session = Depends(get_db)):
    
    movie = db.query(Movie).filter(Movie.title == movie.movie_name).first()

    if not movie:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Movie not found")
    
    movie_review_delete = db.query(Review).filter(Review.movie_id == movie.id).first()

    db.delete(movie_review_delete)
    db.commit()

    return ({"Review sucessfully deleted"})