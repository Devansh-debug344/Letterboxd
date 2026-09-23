from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.schemas.user import CreateUser, UserUpdate
from app.models.user import User
from app.utils import hash_password_async
from app.models.watched import Watched
from app.models.review import Review
from app.models.watchlist import WatchList


async def create_user(user: CreateUser, db: AsyncSession) -> User:
    hashed_password = await hash_password_async(user.password)
    user = User(
        username=user.username,
        email=user.email,
        password=hashed_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(update_user: UserUpdate, user: User, db: AsyncSession) -> User:
    for key, value in update_user.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user(db: AsyncSession):
    result = await db.execute(select(User))
    return list(result.scalars().all())


async def get_user_by_id(user_id: int, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(username: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_profile(id: int, db: AsyncSession) -> User | None:
    return await get_user_by_id(id, db)


async def get_user_stats(user_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(
            select(func.count()).select_from(Watched).where(Watched.user_id == user_id).scalar_subquery(),
            select(func.count()).select_from(Review).where(Review.user_id == user_id).scalar_subquery(),
            select(func.count()).select_from(WatchList).where(WatchList.user_id == user_id).scalar_subquery(),
            select(func.avg(Review.rating)).where(Review.user_id == user_id).scalar_subquery(),
        )
    )
    watched, reviews, watchlist, avg_rating = result.one()

    return {
        "user_id": user_id,
        "watched": watched or 0,
        "reviews": reviews or 0,
        "watchlist": watchlist or 0,
        "avg_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
    }


async def get_public_reviews_by_user(user_id: int, db: AsyncSession, skip: int, limit: int) -> list[Review]:
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.movie), selectinload(Review.user))
        .where(Review.user_id == user_id)
        .order_by(Review.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())