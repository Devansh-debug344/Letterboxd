import httpx
from fastapi import APIRouter , Depends , HTTPException , status
from sqlalchemy.orm import Session
from app.db.session import get_db, run_db
from app.services.fetch_api import fetch_movies_from_api, fetch_movies_from_api_by_search, fetch_movie_collection, fetch_person_from_api, get_cached_movie
from app.schemas.movie import MovieStats
from app.crud.movie import get_movie_stats , get_movie_by_omdb_id , get_movie_by_title ,  save_movie_db

router = APIRouter(prefix="/movies" , tags=['Movies info'] )

from fastapi import Query

@router.get("/search")
async def search_movies(search: str = Query(..., min_length=2) , db : Session = Depends(get_db)):

    movie = await run_db(get_movie_by_title, search, db)
    if movie:
        return movie
    
    data = await fetch_movies_from_api_by_search(search)


    if not data:
        raise HTTPException(status_code=404, detail="Movie not found")

    return data


@router.get("/discover/{collection}")
async def discover_movies(collection: str, page: int = Query(1, ge=1, le=500)):
    if collection not in {"trending", "popular"}:
        raise HTTPException(status_code=404, detail="Collection not found")
    data = await fetch_movie_collection(collection, page)
    return {"items": data["items"], "next": page + 1 if page < data["total_pages"] else None}


@router.get("/person/{person_id}")
async def get_person(person_id: str):
    try:
        return await fetch_person_from_api(person_id)
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Person not found") from error
        raise HTTPException(status_code=502, detail="Person service unavailable") from error


@router.get("/{omdb_id}/stats", response_model=MovieStats)
async def handle_movie_stats(omdb_id: str, db: Session = Depends(get_db)):
    movie = await run_db(get_movie_by_omdb_id, omdb_id, db)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    stats = await run_db(get_movie_stats, movie.id, db)
    return {
        "imdb_id": movie.imdb_id,
        "title": movie.title,
        **stats,
    }


@router.get("/{omdb_id}" , status_code=status.HTTP_200_OK)
async def get_movie(omdb_id: str, db: Session = Depends(get_db)):
    movie = await run_db(get_movie_by_omdb_id, omdb_id, db)
    if movie:
        # The local record powers the app, while OMDb provides detail fields
        # (such as cast) that are not part of the local movie table.
        payload = {column.name: getattr(movie, column.name) for column in movie.__table__.columns}
        cached_details = await get_cached_movie(omdb_id)
        if cached_details:
            payload.update(cached_details)
            payload["id"] = movie.id
        return payload

    try:
        data = await fetch_movies_from_api(omdb_id)
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Movie not found") from error
        raise HTTPException(status_code=502, detail="Movie service unavailable") from error

    # if not data:
    #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    saved_movie = await run_db(save_movie_db, data, db)
    payload = {column.name: getattr(saved_movie, column.name) for column in saved_movie.__table__.columns}
    payload.update(data)
    payload["id"] = saved_movie.id
    return payload
