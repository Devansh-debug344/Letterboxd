from fastapi import APIRouter ,  Depends , HTTPException , status
from app.schemas.watchlist import CreateSaveMovies , SaveMoviesOut , SaveMoviesUpdate , SaveMoviesDelete
from app.schemas.login import DataToken
from app.models.movie import Movie
from app.models.watchlist import WatchList
from sqlalchemy.orm import Session
from app.auth.oauth import get_current_user
from app.db.session import get_db, run_db
from app.crud.movie import get_movie_by_omdb_id , save_movie_db
from app.crud.watchlist import create_save_movie, update_save_movie, get_watchlist_with_movies, del_save_movie_by_movie_id
from app.services.fetch_api import fetch_movies_from_api
from app.schemas.movie import MoviesOut
from typing import Union , List
router = APIRouter(
    prefix='/watchlist',
    tags=['Watchlist']
)

@router.get('/' , response_model=dict)
def handel_get_save_movie(current_user: DataToken = Depends(get_current_user), db: Session = Depends(get_db)):
    
    watchlist_items = get_watchlist_with_movies(current_user.id, db)

    response = [MoviesOut(
           id=movie.id,
           imdb_id=movie.imdb_id,
           title=movie.title,
           genre=movie.genre,
           year=movie.year,
           plot=movie.plot,
           poster=movie.poster,
        ) for _, movie in watchlist_items]
    
    return {"user_id" : current_user.id , "response" : response}

@router.post('/' , response_model=List[Union[SaveMoviesOut , MoviesOut]])
async def handle_save_movie(movie_model: CreateSaveMovies, current_user: DataToken = Depends(get_current_user), db: Session = Depends(get_db)):

    movie = await run_db(get_movie_by_omdb_id, movie_model.omdb_id, db)
    if not movie:
        movie = await fetch_movies_from_api(movie_model.omdb_id)
         
        if movie.get("Response") == "False":
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found from OMDB")

        movie = await run_db(save_movie_db, movie, db)
 
    saved_movie = await run_db(create_save_movie, movie.id, current_user.id, db)

    if not saved_movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "Movie not get saved")

    return [SaveMoviesOut(
        movie_id = saved_movie.id,
        user_id = saved_movie.user_id) 
    , MoviesOut(
        id = movie.id,
        imdb_id=movie.imdb_id,
        title=movie.title,
        genre=movie.genre,
        year=movie.year,
        plot=movie.plot,
        poster=movie.poster,
    )]

@router.delete('/')
def handle_delete_movie(movie_model: CreateSaveMovies, db: Session = Depends(get_db), current_user: DataToken = Depends(get_current_user)):

    movie = get_movie_by_omdb_id(movie_model.omdb_id , db)

    if not movie:
        return {"detail": "Movie was not in watchlist"}
    
    del_mov =  del_save_movie_by_movie_id(movie.id ,current_user.id , db)

    if not del_mov:
        return {"detail": "Movie was not in watchlist"}

    return {"detail": "Movie removed from watchlist successfully"}
