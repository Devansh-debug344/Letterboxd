from app.schemas.watchlist import CreateSaveMovies , SaveMoviesUpdate
from sqlalchemy.orm import Session
from fastapi import Depends , HTTPException , status
from app.db.upsert import insert_ignore
from app.models.watchlist import WatchList
from app.models.movie import Movie

def create_save_movie(movie_id : int , user_id : int , db : Session):
    statement = insert_ignore(
        db,
        WatchList,
        "uq_watchlist_user_movie",
        user_id=user_id,
        movie_id=movie_id,
    )
    db.execute(statement)
    db.commit()
    return db.query(WatchList).filter(
        WatchList.movie_id == movie_id,
        WatchList.user_id == user_id,
    ).first()




def update_save_movie(movie : SaveMoviesUpdate , watchlist : WatchList , db : Session):
    
    for key , value in movie.model_dump(exclude_unset=True).items():
        setattr(watchlist , key , value)
        
    db.commit()
    db.refresh(watchlist)

    return watchlist



    
def get_save_movie(user_id : int , db : Session):
    return db.query(WatchList).filter(WatchList.user_id ==user_id).all()


def get_watchlist_with_movies(user_id: int, db: Session):
    return (
        db.query(WatchList, Movie)
        .join(Movie, Movie.id == WatchList.movie_id)
        .filter(WatchList.user_id == user_id)
        .order_by(WatchList.created_at.desc())
        .all()
    )


def del_save_movie_by_movie_id(movie_id : int , user_id:int ,  db : Session):
    movie_deleted = db.query(WatchList).filter(WatchList.user_id == user_id , WatchList.movie_id == movie_id).first()

    if movie_deleted:
     db.delete(movie_deleted)
     db.commit()
     return True

    return False
