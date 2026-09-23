import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.watched import WatchedCreate, WatchedOut
from app.schemas.login import DataToken
from app.crud.movie import get_movie_by_omdb_id, save_movie_db
from app.crud.watched import add_movie_watched, get_watched_movie, get_del_watched_movies_by_id
from app.auth.oauth import get_current_user
from app.services.fetch_api import fetch_movies_from_api
from app.services.rate_limiter import rate_limiter
from app.services.cache import get_json, set_json, invalidate

router = APIRouter(prefix="/watched", tags=["watched"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=WatchedOut)
async def add_watched(
    body: WatchedCreate,
    db: AsyncSession = Depends(get_db),
    current_user: DataToken = Depends(get_current_user),
    request: Request = None,
):
    await rate_limiter.enforce(request, "watched:create", user_id=current_user.id, max_attempts=30, window_seconds=60)
    movie = await get_movie_by_omdb_id(body.omdb_id, db)

    if not movie:
        try:
            response = await fetch_movies_from_api(body.omdb_id)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Movie not found")
            raise HTTPException(status_code=502, detail="Movie service unavailable") from error

        movie = await save_movie_db(response, db)

    added_movie = await add_movie_watched(current_user.id, movie.id, body.rating, body.watched_at, db)

    await invalidate(
        f"movie:{body.omdb_id}:stats",
        f"movie:{body.omdb_id}",
        f"user:{current_user.id}:stats",
        f"user:{current_user.id}:watched",
        f"user:{current_user.id}:watchlist",
    )

    return WatchedOut(
        id=added_movie.id,
        omdb_id=body.omdb_id,
        title=movie.title,
        year=movie.year,
        poster=movie.poster,
        rating=added_movie.rating,
        watched_at=added_movie.watched_at,
    )


@router.get("/", status_code=status.HTTP_200_OK)
async def my_watched(
    db: AsyncSession = Depends(get_db),
    current_user: DataToken = Depends(get_current_user),
    request: Request = None,
):
    await rate_limiter.enforce(request, "watched:reads", user_id=current_user.id, max_attempts=120, window_seconds=60)
    cache_key = f"user:{current_user.id}:watched"
    cached = await get_json(cache_key)
    if cached is not None:
        return cached

    items = await get_watched_movie(current_user.id, db)
    ls = [{"id": item.id, "movie_id": item.movie_id} for item in items]
    await set_json(cache_key, ls, ttl_seconds=300)
    return ls


@router.delete("/{omdb_id}", status_code=status.HTTP_200_OK)
async def remove_watched(
    omdb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: DataToken = Depends(get_current_user),
    request: Request = None,
):
    await rate_limiter.enforce(request, "watched:delete", user_id=current_user.id, max_attempts=60, window_seconds=60)
    movie = await get_movie_by_omdb_id(omdb_id, db)
    if not movie:
        return {"detail": "Movie was not in watched"}
    del_movie = await get_del_watched_movies_by_id(current_user.id, movie.id, db)
    if not del_movie:
        return {"detail": "Movie was not in watched"}

    await invalidate(
        f"movie:{omdb_id}:stats",
        f"movie:{omdb_id}",
        f"user:{current_user.id}:stats",
        f"user:{current_user.id}:watched",
    )

    return {"detail": "Movie removed from watched successfully"}