from app.schemas.watchlist import CreateSaveMovies , SaveMoviesUpdate
from sqlalchemy.orm import Session
from fastapi import Depends , HTTPException , status
from app.models.watchlist import WatchList
from app.models.movie import Movie
from app.models.watched import Watched
from app.crud.watchlist import del_save_movie_by_movie_id
from datetime import datetime
def get_watched_movies_by_id(user_id : int , movie_id : int , db : Session):
    return db.query(Watched).filter(Watched.user_id == user_id, Watched.movie_id == movie_id).first()

def get_watched_movies_by_id(user_id : int , movie_id : int , db : Session):
    movie = db.query(Watched).filter(Watched.user_id == user_id, Watched.movie_id == movie_id).first()

    return movie

def get_del_watched_movies_by_id(user_id : int , movie_id : int , db : Session):
    movie = db.query(Watched).filter(Watched.user_id == user_id, Watched.movie_id == movie_id).first()

    db.delete(movie)
    db.commit()

    return movie

def add_movie_watched(user_id : int , movie_id : int , rating : float | None = None , watched_at : datetime| None = None , db : Session | None = None):


    item = Watched(
        user_id=user_id,
        movie_id=movie_id,
        rating=rating,
        watched_at=watched_at,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return item

def get_watched_movie(user_id : int , db : Session):
    return  db.query(Watched).filter(Watched.user_id == user_id).order_by(Watched.watched_at.desc()).all()