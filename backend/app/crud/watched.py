from app.schemas.watchlist import CreateSaveMovies , SaveMoviesUpdate
from sqlalchemy.orm import Session
from fastapi import Depends , HTTPException , status
from app.models.watchlist import WatchList
from app.models.movie import Movie
from app.models.watched import Watched
from app.crud.watchlist import del_save_movie_by_movie_id
from app.db.upsert import insert_ignore
from datetime import datetime, timezone
def get_watched_movies_by_id(user_id : int , movie_id : int , db : Session):
    return db.query(Watched).filter(Watched.user_id == user_id, Watched.movie_id == movie_id).first()

def get_del_watched_movies_by_id(user_id : int , movie_id : int , db : Session):
    movie = db.query(Watched).filter(Watched.user_id == user_id, Watched.movie_id == movie_id).first()

    if not movie:
        return None
    db.delete(movie)
    db.commit()

    return movie

def add_movie_watched(user_id : int , movie_id : int , rating : float | None = None , watched_at : datetime| None = None , db : Session | None = None):
    if watched_at is None:
        watched_at = datetime.now(timezone.utc)
    statement = insert_ignore(
        db,
        Watched,
        "uq_watched_user_movie",
        user_id=user_id,
        movie_id=movie_id,
        rating=rating,
        watched_at=watched_at,
    )
    db.execute(statement)
    db.query(WatchList).filter(WatchList.user_id == user_id, WatchList.movie_id == movie_id).delete(synchronize_session=False)
    db.commit()
    return get_watched_movies_by_id(user_id, movie_id, db)

def get_watched_movie(user_id : int , db : Session):
    return db.query(Watched).filter(Watched.user_id == user_id).order_by(Watched.watched_at.desc()).all()