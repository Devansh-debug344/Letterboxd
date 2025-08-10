from fastapi import APIRouter ,  Depends , HTTPException , status
from app.schemas.watchlist import CreateSaveMovies , SaveMoviesOut , SaveMoviesUpdate , SaveMoviesDelete
from app.models.user import User
from app.models.movie import Movie
from app.models.watchlist import WatchList
from sqlalchemy.orm import Session
from app.auth.oauth import get_current_user
from app.db.session import get_db
from app.crud.watchlist import create_save_movie , save_movie_db , update_save_movie , get_save_movie
from app.services.fetch_api import fetch_movies_from_api
from typing import List
router = APIRouter(
    prefix='/watchlist',
    tags=['Watchlist']
)

@router.get('/' , response_model=List[SaveMoviesOut])
def handel_get_save_movie(current_user : User = Depends(get_current_user) , db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "User not found")
    
    watchlist_items =  get_save_movie(user_id = current_user.id , db=db)

    response = []
    for item in watchlist_items:
        response.append(SaveMoviesOut(
            movie_id=item.movie_id,
            movie_name=item.movie.title,
            user_name=current_user.username,
            note = item.note,
            status=item.status
        ))
    
    return response

@router.post('/' , response_model=SaveMoviesOut)
async def handle_save_movie(movie_model : CreateSaveMovies , current_user : User = Depends(get_current_user) , db : Session = Depends(get_db)):
     
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "User not found")
    
    response = await fetch_movies_from_api(name = movie_model.movie_name)

    if response.get("Response") == "False":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found from OMDB")

    save_movie_db(response = response , db=db)

    movie = db.query(Movie).filter(Movie.title == movie_model.movie_name).first()

    if not movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "Movie not found")
 
    saved_movie = create_save_movie(movie_id = movie.id , user_id = user.id , db=db )

    return SaveMoviesOut(
        movie_id = movie.id,
        movie_name=movie.title,
        user_name=user.username,
        note = saved_movie.note,
        status=saved_movie.status
    )

@router.patch('/')
def handle_update_save_movie(update_movie : SaveMoviesUpdate , current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "User not found")
    
    movie = db.query(Movie).filter(Movie.title == update_movie.movie_name).first()
    if not movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "Movie not found")
    watchlist = db.query(WatchList).filter(WatchList.movie_id == movie.id).first()
    if not movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "Movie not found in watch list")
 
    update_save_movie(movie = update_movie  , watchlist = watchlist , db = db)

    return {"Movie updated Succesfully"}

@router.delete('/')
def handle_delete_movie(movie_model : SaveMoviesDelete , db : Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.title == movie_model.movie_name).first()
    if not movie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail = "Movie not found in watchlist")
    
    
    movie_deleted = db.query(WatchList).filter(WatchList.movie_id == movie.id).first()

    db.delete(movie_deleted)
    db.commit()
   
    return {"detail": "Movie removed from watchlist successfully"}