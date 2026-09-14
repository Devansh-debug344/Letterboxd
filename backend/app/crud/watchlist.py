from app.schemas.watchlist import CreateSaveMovies , SaveMoviesUpdate
from sqlalchemy.orm import Session
from fastapi import Depends , HTTPException , status
from app.models.watchlist import WatchList
from app.models.movie import Movie

def create_save_movie(movie_id : int , user_id : int , db : Session):
    
    existing_movie = db.query(WatchList).filter(WatchList.movie_id == movie_id).first()

    if existing_movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "Movie already saved")
    
    saved_movie = WatchList(user_id = user_id , movie_id = movie_id)
    db.add(saved_movie)
    db.commit()
    db.refresh(saved_movie)

    return saved_movie




def update_save_movie(movie : SaveMoviesUpdate , watchlist : WatchList , db : Session):
    
    for key , value in movie.model_dump(exclude_unset=True).items():
        setattr(watchlist , key , value)
        
    db.commit()
    db.refresh(watchlist)

    return watchlist



    
def get_save_movie(user_id : int , db : Session):
    return db.query(WatchList).filter(WatchList.user_id ==user_id).all()


def del_save_movie_by_movie_id(movie_id : int , user_id:int ,  db : Session):
    movie_deleted = db.query(WatchList).filter(WatchList.user_id == user_id , WatchList.movie_id == movie_id).first()

    if movie_deleted:
     db.delete(movie_deleted)
     db.commit()
