from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.auth.oauth import get_current_user
from app.schemas.review import ReviewCreate, ReviewDelete, ReviewOut, ReviewUpdate
from app.crud.movie import get_movie_by_omdb_id , save_movie_db
from app.services.fetch_api import fetch_movies_from_api
from app.crud.review import (
    get_reviews_by_user,
    create_review,
    update_review,
    delete_review,
    to_review_out,
    get_reviews_by_movie
)

router = APIRouter(prefix="/review", tags=["Reviews"])


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def handle_create_review(
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    movie = get_movie_by_omdb_id(body.omdb_id, db) 
    
    if not movie:
        response = await fetch_movies_from_api(body.omdb_id)
            
        if response.get("Response") == "False":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found from OMDB")
         
        movie = save_movie_db(response , db)

    item = create_review(current_user.id, movie.id, body, db)
    return to_review_out(item)


@router.patch("/", response_model=ReviewOut)
def handle_update_review(
    body: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    movie = get_movie_by_omdb_id(body.omdb_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    item = update_review(current_user.id, movie.id, body, db)
    return to_review_out(item)


@router.get("/", response_model=list[ReviewOut])
def handle_get_review(
    omdb_id: str | None = Query(None),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    movie_id = None
    if omdb_id:
        movie = get_movie_by_omdb_id(omdb_id, db)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        movie_id = movie.id
    skip = (page - 1) * limit
    items = get_reviews_by_user(current_user.id, db, skip , limit ,  movie_id)
    return [to_review_out(r) for r in items]


@router.delete("/")
def handle_delete_review(
    body: ReviewDelete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    movie = get_movie_by_omdb_id(body.omdb_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    delete_review(current_user.id, movie.id, db)

    return {"detail": "Review deleted"}


@router.get("/movie/{omdb_id}", response_model=list[ReviewOut])
def handle_get_movie_reviews(
    omdb_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    movie = get_movie_by_omdb_id(omdb_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    skip = (page - 1) * limit
    items = get_reviews_by_movie(movie.id, db, skip, limit)
    return [to_review_out(r) for r in items]