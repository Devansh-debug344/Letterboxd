from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import CreateUser, UserOut, UserProfile, UserUpdate, UserStats
from app.schemas.login import DataToken
from app.db.session import get_db
from app.services.rate_limiter import rate_limiter
from app.crud.user import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    get_user_profile,
    update_user,
    get_user_by_id,
    get_user_stats,
    get_public_reviews_by_user,
)
from app.auth.oauth import get_current_user
from app.models.user import User
from typing import List
from app.schemas.review import ReviewOut
from app.crud.review import to_review_out
from app.services.cache import get_json, set_json, invalidate

router = APIRouter(
    prefix="/user",
    tags=['Users'],
)


@router.post("/", response_model=UserOut)
async def create_users(user_details: CreateUser, db: AsyncSession = Depends(get_db), request: Request = None):
    await rate_limiter.enforce(
        request,
        "register",
        max_attempts=5,
        window_seconds=3600,
        detail="Too many accounts created from this address. Please try again later.",
    )
    if await get_user_by_username(user_details.username, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with same username already existed. Try another username.")
    if await get_user_by_email(user_details.email, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already existed")
    return await create_user(user_details, db)


@router.get('/profile', response_model=UserProfile)
async def get_profile(db: AsyncSession = Depends(get_db), current_user: DataToken = Depends(get_current_user), request: Request = None):
    await rate_limiter.enforce(request, "user:reads", user_id=current_user.id, max_attempts=120, window_seconds=60)
    return await get_user_profile(current_user.id, db)


@router.patch('/profile', response_model=UserUpdate)
async def handle_update_user(
    user_details: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: DataToken = Depends(get_current_user),
    request: Request = None,
):
    await rate_limiter.enforce(request, "profile:update", user_id=current_user.id, max_attempts=10, window_seconds=60)
    user = await get_user_by_id(current_user.id, db)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_user = await update_user(user_details, user, db)

    await invalidate(f"user:{current_user.id}:stats")

    return updated_user


@router.get("/{user_id}/stats", response_model=UserStats, status_code=status.HTTP_200_OK)
async def handle_user_stats(user_id: int, db: AsyncSession = Depends(get_db), request: Request = None):
    await rate_limiter.enforce(request, "user:reads", max_attempts=120, window_seconds=60)
    cache_key = f"user:{user_id}:stats"
    cached = await get_json(cache_key)
    if cached is not None:
        return cached

    if not await get_user_by_id(user_id, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    stats = await get_user_stats(user_id, db)
    await set_json(cache_key, stats, ttl_seconds=300)
    return stats


@router.get("/{user_id}/reviews", response_model=List[ReviewOut], status_code=status.HTTP_200_OK)
async def handle_user_reviews(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    await rate_limiter.enforce(request, "user:reads", max_attempts=120, window_seconds=60)
    if not await get_user_by_id(user_id, db):
        raise HTTPException(status_code=404, detail="User not found")

    skip = (page - 1) * limit
    items = await get_public_reviews_by_user(user_id, db, skip, limit)
    return [to_review_out(r) for r in items]