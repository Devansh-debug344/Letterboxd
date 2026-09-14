from fastapi import APIRouter , Depends , HTTPException , status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.fetch_api import fetch_movies_from_api , fetch_movies_from_api_by_search 
from app.schemas.movie import MovieStats
from app.crud.movie import get_movie_stats , get_movie_by_omdb_id , get_movie_by_title ,  save_movie_db

router = APIRouter(prefix="/movies" , tags=['Movies info'] )

from fastapi import Query

@router.get("/search")
async def search_movies(search: str = Query(..., min_length=2) , db : Session = Depends(get_db)):

    movie = get_movie_by_title(search , db)
    if movie:
        return movie
    
    data = await fetch_movies_from_api_by_search(search)


    if not data or data.get("Response") == "False":
        raise HTTPException(status_code=404, detail="Movie not found")

    return data.get("Search", [])


@router.get("/{omdb_id}/stats", response_model=MovieStats)
def handle_movie_stats(omdb_id: str, db: Session = Depends(get_db)):
    movie = get_movie_by_omdb_id(omdb_id, db)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    stats = get_movie_stats(movie.id, db)
    return {
        "imdb_id": movie.imdb_id,
        "title": movie.title,
        **stats,
    }


@router.get("/{omdb_id}" , status_code=status.HTTP_200_OK)
async def get_movie(omdb_id: str, db: Session = Depends(get_db)):
    movie = get_movie_by_omdb_id(omdb_id, db)
    if movie:
        return movie

    data = await fetch_movies_from_api(omdb_id)

    if not data or data.get("Response") == "False":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    save_movie_db(data , db)
          
    return data