from app.schemas.watchlist import CreateSaveMovies , SaveMoviesUpdate
from sqlalchemy.orm import Session
from fastapi import Depends , HTTPException , status
from app.db.session import get_db
from app.models.watchlist import WatchList
from app.models.movie import Movie

def create_save_movie(movie_id : int , user_id : int , db : Session = Depends(get_db)):
    
    existing_movie = db.query(WatchList).filter(WatchList.movie_id == movie_id).first()

    if existing_movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "Movie already saved")
    
    saved_movie = WatchList(user_id = user_id , movie_id = movie_id)
    db.add(saved_movie)
    db.commit()
    db.refresh(saved_movie)

    return saved_movie

def save_movie_db(response : dict , db : Session = Depends(get_db)):
    
    existing_movie = db.query(Movie).filter(Movie.imdb_id == response.get("imdbID")).first()

    if existing_movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="Movie already saved in db")

    movie = Movie(
         imdb_id = response.get("imdbID"),
         title = response.get("Title"),
         year = response.get('Year'),
         genre = response.get('Genre'),
         poster = response.get('Poster'),
         plot =  response.get('Plot'),
         imdbRating = response.get('imdbRating'),
         type = response.get('Type'),
         awards = response.get('Awards'),
         language = response.get('Language'),
         runtime = response.get('Runtime'),
         released = response.get('Released')
    )

    db.add(movie)
    db.commit()
    db.refresh(movie)

    return movie

def update_save_movie(movie : SaveMoviesUpdate , watchlist : WatchList , db : Session = Depends(get_db)):
    
    for key , value in movie.dict(exclude_unset=True).items():
        setattr(watchlist , key , value)
        
    db.commit()
    db.refresh(watchlist)

    return watchlist
    
def get_save_movie(user_id : int , db : Session = Depends(get_db)):
    return db.query(WatchList).filter(WatchList.user_id ==user_id).all()
