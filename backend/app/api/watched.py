from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db, run_db
from app.models.watched import Watched
from app.schemas.watched import WatchedCreate , WatchedOut
from app.schemas.login import DataToken
from app.crud.movie import get_movie_by_omdb_id , save_movie_db 
from app.crud.watched import add_movie_watched, get_watched_movie , get_del_watched_movies_by_id
from app.auth.oauth import get_current_user
from app.services.fetch_api import fetch_movies_from_api

router = APIRouter(prefix="/watched", tags=["watched"])


@router.post("/", status_code=status.HTTP_201_CREATED , response_model=WatchedOut)
async def add_watched(body: WatchedCreate, db: Session = Depends(get_db), current_user: DataToken = Depends(get_current_user)):

    movie = await run_db(get_movie_by_omdb_id, body.omdb_id, db)

    if not movie:
        response = await fetch_movies_from_api(body.omdb_id)
        
        if response.get("Response") == "False":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found from OMDB")
        
        movie = await run_db(save_movie_db, response, db)
         
    added_movie = await run_db(add_movie_watched, current_user.id, movie.id, body.rating, body.watched_at, db)

    return WatchedOut(
        id = added_movie.id,
        omdb_id= body.omdb_id,
        title=movie.title,
        year=movie.year,
        poster=movie.poster,
        rating=added_movie.rating,
        watched_at=added_movie.watched_at
    )

@router.get("/" , status_code=status.HTTP_200_OK)
def my_watched(
    db: Session = Depends(get_db),
    current_user: DataToken = Depends(get_current_user),
):
    
    items = get_watched_movie(current_user.id , db)
    ls = []
    for item in items:
        ls.append({"id" : item.id , "movie_id" :item.movie_id})
    return ls

@router.delete("/{omdb_id}", status_code=status.HTTP_200_OK)
def remove_watched(
    omdb_id: str,
    db: Session = Depends(get_db),
    current_user: DataToken = Depends(get_current_user),
):

    movie = get_movie_by_omdb_id(omdb_id, db)  
    if not movie:
        return {"detail": "Movie was not in watched"}
    del_movie = get_del_watched_movies_by_id(current_user.id , movie.id, db)
    if not del_movie:
        return {"detail": "Movie was not in watched"}

    return {"detail": "Movie removed from watched successfully"}