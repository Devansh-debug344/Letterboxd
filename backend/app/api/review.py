import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.login import DataToken
from app.auth.oauth import get_current_user
from app.schemas.review import ReviewCreate, ReviewDelete, ReviewOut, ReviewUpdate
from app.crud.movie import get_movie_by_omdb_id, save_movie_db
from app.services.fetch_api import fetch_movies_from_api
from app.services.rate_limiter import rate_limiter
from app.crud.review import (
    get_reviews_by_user,
    create_review,
    update_review,
    delete_review,
    to_review_out,
    get_reviews_by_movie,
)
from app.services.cache import get_json, set_json, get_version, bump_version, invalidate

router = APIRouter(prefix="/review", tags=["Reviews"])


async def _invalidate_related(omdb_id: str, user_id: int) -> None:
    await invalidate(
        f"movie:{omdb_id}:stats",
        f"movie:{omdb_id}",
        f"user:{user_id}:stats",
    )
    await bump_version(f"user:{user_id}:reviews", f"movie:{omdb_id}:reviews")


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def handle_create_review(
    body: ReviewCreate,
    current_user: DataToken = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    await rate_limiter.enforce(request, "review:create", user_id=current_user.id, max_attempts=30, window_seconds=60)
    movie = await get_movie_by_omdb_id(body.omdb_id, db)

    if not movie:
        try:
            response = await fetch_movies_from_api(body.omdb_id)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Movie not found")
            raise HTTPException(status_code=502, detail="Movie service unavailable") from error

        movie = await save_movie_db(response, db)

    item = await create_review(current_user.id, movie.id, body, db)
    await _invalidate_related(body.omdb_id, current_user.id)
    return to_review_out(item)


@router.patch("/", response_model=ReviewOut)
async def handle_update_review(
    body: ReviewUpdate,
    current_user: DataToken = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    await rate_limiter.enforce(request, "review:update", user_id=current_user.id, max_attempts=30, window_seconds=60)
    movie = await get_movie_by_omdb_id(body.omdb_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    item = await update_review(current_user.id, movie.id, body, db)
    await _invalidate_related(body.omdb_id, current_user.id)
    return to_review_out(item)


@router.get("/", response_model=list[ReviewOut])
async def handle_get_review(
    omdb_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: DataToken = Depends(get_current_user),
    request: Request = None,
):
    await rate_limiter.enforce(request, "review:reads", user_id=current_user.id, max_attempts=120, window_seconds=60)
    movie_id = None
    if omdb_id:
        movie = await get_movie_by_omdb_id(omdb_id, db)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        movie_id = movie.id

    version = await get_version(f"user:{current_user.id}:reviews")
    cache_key = f"user:{current_user.id}:reviews:v{version}:{movie_id or 'all'}:{page}:{limit}"
    cached = await get_json(cache_key)
    if cached is not None:
        return cached

    skip = (page - 1) * limit
    items = await get_reviews_by_user(current_user.id, db, skip, limit, movie_id)
    payload = [to_review_out(r).model_dump(mode="json") for r in items]
    await set_json(cache_key, payload, ttl_seconds=300)
    return payload


@router.delete("/")
async def handle_delete_review(
    body: ReviewDelete,
    current_user: DataToken = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    await rate_limiter.enforce(request, "review:delete", user_id=current_user.id, max_attempts=60, window_seconds=60)
    movie = await get_movie_by_omdb_id(body.omdb_id, db)
    if not movie:
        return {"detail": "Review was not present"}
    await delete_review(current_user.id, movie.id, db)
    await _invalidate_related(body.omdb_id, current_user.id)
    return {"detail": "Review deleted"}


@router.get("/movie/{omdb_id}", response_model=list[ReviewOut])
async def handle_get_movie_reviews(
    omdb_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    await rate_limiter.enforce(request, "movie:reviews:reads", max_attempts=120, window_seconds=60)
    movie = await get_movie_by_omdb_id(omdb_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    version = await get_version(f"movie:{omdb_id}:reviews")
    cache_key = f"movie:{omdb_id}:reviews:v{version}:{page}:{limit}"
    cached = await get_json(cache_key)
    if cached is not None:
        return cached

    skip = (page - 1) * limit
    items = await get_reviews_by_movie(movie.id, db, skip, limit)
    payload = [to_review_out(r).model_dump(mode="json") for r in items]
    await set_json(cache_key, payload, ttl_seconds=300)
    return payload