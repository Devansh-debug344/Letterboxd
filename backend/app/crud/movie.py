from sqlalchemy import func
from app.models.review import Review
from app.models.movie import Movie
from app.models.watched import Watched
from app.models.watchlist import WatchList
from sqlalchemy.orm import Session


def get_movie_stats(movie_id: int, db: Session) -> dict:
    review_count = db.query(func.count(Review.id)).filter(Review.movie_id == movie_id).scalar()
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.movie_id == movie_id).scalar()
    watched_count = db.query(func.count(Watched.id)).filter(Watched.movie_id == movie_id).scalar()
    watchlist_count = db.query(func.count(WatchList.id)).filter(WatchList.movie_id == movie_id).scalar()

    return {
        "review_count": review_count or 0,
        "avg_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
        "watched_count": watched_count or 0,
        "watchlist_count": watchlist_count or 0,
    }