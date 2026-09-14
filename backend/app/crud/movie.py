from sqlalchemy import func
from app.models.review import Review
from app.models.movie import Movie
from app.models.watched import Watched
from app.models.watchlist import WatchList
from sqlalchemy.orm import Session

def save_movie_db(response : dict , db : Session):
    
    existing_movie = db.query(Movie).filter(Movie.imdb_id == response.get("imdbID")).first()

    if not existing_movie:
        
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
    return existing_movie

def get_movie_by_omdb_id(id : str , db : Session):
    movie = db.query(Movie).filter(Movie.imdb_id == id).first()
    return movie

def get_movie_by_title(title : str , db : Session):
    movie = db.query(Movie).filter(Movie.title == title).first()
    return movie


def get_movie_by_id(id : int , db : Session):
    movie = db.query(Movie).filter(Movie.id == id).first()
    return movie


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