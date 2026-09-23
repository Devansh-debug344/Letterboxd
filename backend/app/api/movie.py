import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.rate_limiter import rate_limiter
from app.services.fetch_api import (
    fetch_movies_from_api,
    fetch_movies_from_api_by_search,
    fetch_movie_collection,
    fetch_person_from_api,
    get_cached_movie,
)
from app.schemas.movie import MovieStats , MoviesOut
from app.crud.movie import get_movie_stats, get_movie_by_omdb_id, get_movie_by_title, save_movie_db
from app.services.cache import get_json, set_json

router = APIRouter(prefix="/movies", tags=['Movies info'])


@router.get("/search")
async def search_movies(search: str = Query(..., min_length=2), db: AsyncSession = Depends(get_db), request: Request = None):
    await rate_limiter.enforce(
        request,
        "search",
        max_attempts=10,
        window_seconds=60,
        detail="Too many searches. Please try again in a minute.",
    )
    movie = await get_movie_by_title(search, db)
    if movie:
        return movie

    data = await fetch_movies_from_api_by_search(search)

    if not data:
        raise HTTPException(status_code=404, detail="Movie not found")

    return data


@router.get("/discover/{collection}")
async def discover_movies(collection: str, page: int = Query(1, ge=1, le=500), request: Request = None):
    if collection not in {"trending", "popular"}:
        raise HTTPException(status_code=404, detail="Collection not found")
    await rate_limiter.enforce(
        request,
        "discover",
        max_attempts=10,
        window_seconds=60,
        detail="Too many discovery requests. Please try again in a minute.",
    )
    data = await fetch_movie_collection(collection, page)
    return {"items": data["items"], "next": page + 1 if page < data["total_pages"] else None}


@router.get("/person/{person_id}")
async def get_person(person_id: str, request: Request = None):
    await rate_limiter.enforce(
        request,
        "person",
        max_attempts=10,
        window_seconds=60,
        detail="Too many requests. Please try again in a minute.",
    )
    try:
        return await fetch_person_from_api(person_id)
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Person not found") from error
        raise HTTPException(status_code=502, detail="Person service unavailable") from error


@router.get("/{omdb_id}/stats", response_model=MovieStats)
async def handle_movie_stats(omdb_id: str, db: AsyncSession = Depends(get_db), request: Request = None):
    await rate_limiter.enforce(request, "movie:reads", max_attempts=120, window_seconds=60)
    cache_key = f"movie:{omdb_id}:stats"
    cached = await get_json(cache_key)
    if cached is not None:
        return cached

    movie = await get_movie_by_omdb_id(omdb_id, db)
    if not movie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    stats = await get_movie_stats(movie.id, db)
    payload = {
        "imdb_id": movie.imdb_id,
        "title": movie.title,
        **stats,
    }
    await set_json(cache_key, payload, ttl_seconds=300)
    return payload


@router.get("/{omdb_id}", status_code=status.HTTP_200_OK , response_model=MoviesOut)
async def get_movie(omdb_id: str, db: AsyncSession = Depends(get_db), request: Request = None):
    await rate_limiter.enforce(
        request,
        "movie",
        max_attempts=30,
        window_seconds=60,
        detail="Too many requests. Please try again in a minute.",
    )
    cache_key = f"movie:{omdb_id}"
    cached = await get_json(cache_key)
    if cached is not None:
        return cached

    movie = await get_movie_by_omdb_id(omdb_id, db)
    if movie:
        payload = MoviesOut.model_validate(movie)
        await set_json(cache_key, payload, ttl_seconds=300)
        return payload

    cached_tmdb_details = await get_cached_movie(omdb_id)

    if cached_tmdb_details is None:
        try:
            data = await fetch_movies_from_api(omdb_id)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Movie not found") from error
            raise HTTPException(status_code=502, detail="Movie service unavailable") from error
    else:
        data = cached_tmdb_details

    saved_movie = await save_movie_db(data, db)
    payload = MoviesOut.model_validate(saved_movie)
    await set_json(cache_key, payload, ttl_seconds=300)
    return payload