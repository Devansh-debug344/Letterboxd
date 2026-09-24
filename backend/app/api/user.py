from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import CreateUser, UserOut, UserProfile, UserUpdate, UserStats
from app.schemas.login import DataToken
from app.db.session import get_db
from app.services.rate_limiter import rate_limiter
from app.services.cloudinary_service import cloudinary_configured, delete_image, upload_image
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
from uuid import uuid4

router = APIRouter(
    prefix="/user",
    tags=['Users'],
)

MAX_AVATAR_BYTES = 5 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _avatar_public_id(url: str | None) -> str | None:
    """Reconstruct the Cloudinary public id (folder included) from an asset URL."""
    if not url or "res.cloudinary.com" not in url:
        return None
    parts = url.split("/")
    try:
        idx = parts.index("upload")
    except ValueError:
        return None
    tail = "/".join(parts[idx + 2:])
    return tail.rsplit(".", 1)[0] or None


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


@router.post("/avatar", response_model=UserProfile)
async def upload_avatar(
    current_user: DataToken = Depends(get_current_user),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    if not cloudinary_configured():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Media uploads are not configured.")

    await rate_limiter.enforce(request, "avatar:upload", user_id=current_user.id, max_attempts=10, window_seconds=60)

    content_type = file.content_type or ""
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG and WebP images are allowed.",
        )

    data = await file.read(MAX_AVATAR_BYTES + 1)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file is too large (max 5 MB).",
        )

    user = await get_user_by_id(current_user.id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    previous_public_id = _avatar_public_id(user.avatar_url)

    public_id = f"user_{current_user.id}/avatar/{uuid4().hex}"
    try:
        result = upload_image(data, folder="avatars", public_id=public_id, resource_type="image")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Avatar upload failed.") from exc

    user.avatar_url = result.get("secure_url")
    await db.commit()
    await db.refresh(user)

    if previous_public_id and previous_public_id != result.get("public_id"):
        try:
            delete_image(previous_public_id)
        except Exception:
            pass

    await invalidate(f"user:{current_user.id}:stats")
    return user


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