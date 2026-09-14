from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.review import Review
from app.models.movie import Movie
from app.schemas.review import ReviewCreate, ReviewUpdate


def get_movie_by_imdb_id(imdb_id: str, db: Session) -> Movie | None:
    return db.query(Movie).filter(Movie.imdb_id == imdb_id).first()


def get_review_by_user_movie(user_id: int, movie_id: int, db: Session) -> Review | None:
    return (
        db.query(Review)
        .filter(Review.user_id == user_id, Review.movie_id == movie_id)
        .first()
    )


def get_reviews_by_user(user_id: int, db: Session, skip : int , limit : int , movie_id: int | None = None) -> list[Review]:
    q = db.query(Review).filter(Review.user_id == user_id)
    if movie_id:
        q = q.filter(Review.movie_id == movie_id)
    return q.order_by(Review.updated_at.desc()).offset(skip).limit(limit).all()


def create_review(user_id: int, movie_id: int, data: ReviewCreate, db: Session) -> Review:
    item = Review(
        user_id=user_id,
        movie_id=movie_id,
        rating=data.rating,
        review=data.review,
        spoiler=data.spoiler,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review already exists")
    db.refresh(item)
    return item


def update_review(user_id: int, movie_id: int, data: ReviewUpdate, db: Session) -> Review:
    item = get_review_by_user_movie(user_id, movie_id, db)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if data.rating is not None:
        item.rating = data.rating
    if data.review is not None:
        item.review = data.review
    if data.spoiler is not None:
        item.spoiler = data.spoiler

    db.commit()
    db.refresh(item)
    return item


def delete_review(user_id: int, movie_id: int, db: Session) -> None:
    item = get_review_by_user_movie(user_id, movie_id, db)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    db.delete(item)
    db.commit()


def to_review_out(item: Review) -> dict:
    return {
        "id": item.id,
        "movie_id": item.movie_id,
        "user_id": item.user_id,
        "movie_name": item.movie.title,
        "user_name": item.user.username,
        "rating": item.rating,
        "review": item.review,
        "likes": item.likes,
        "updated_at": item.updated_at,
    }


def get_reviews_by_movie(movie_id: int, db: Session, skip: int, limit: int) -> list[Review]:
    return (
        db.query(Review)
        .filter(Review.movie_id == movie_id)
        .order_by(Review.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_reviews_by_movie(movie_id: int, db: Session) -> int:
    return db.query(Review).filter(Review.movie_id == movie_id).count()