from datetime import datetime, timezone
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.watchlist import WatchList
from app.models.watched import Watched
from app.db.upsert import insert_ignore


async def get_watched_movies_by_id(user_id: int, movie_id: int, db: AsyncSession) -> Watched | None:
    result = await db.execute(
        select(Watched).where(Watched.user_id == user_id, Watched.movie_id == movie_id)
    )
    return result.scalar_one_or_none()


async def get_del_watched_movies_by_id(user_id: int, movie_id: int, db: AsyncSession) -> Watched | None:
    movie = await get_watched_movies_by_id(user_id, movie_id, db)
    if not movie:
        return None
    await db.delete(movie)
    await db.commit()
    return movie


async def add_movie_watched(
    user_id: int,
    movie_id: int,
    rating: float | None = None,
    watched_at: datetime | None = None,
    db: AsyncSession | None = None,
) -> Watched | None:
    if watched_at is None:
        watched_at = datetime.now(timezone.utc)
    statement = insert_ignore(
        db,
        Watched,
        "uq_watched_user_movie",
        user_id=user_id,
        movie_id=movie_id,
        rating=rating,
        watched_at=watched_at,
    )
    await db.execute(statement)
    await db.execute(
        delete(WatchList).where(
            WatchList.user_id == user_id,
            WatchList.movie_id == movie_id,
        )
    )
    await db.commit()
    return await get_watched_movies_by_id(user_id, movie_id, db)


async def get_watched_movie(user_id: int, db: AsyncSession) -> list[Watched]:
    result = await db.execute(
        select(Watched).where(Watched.user_id == user_id).order_by(Watched.watched_at.desc())
    )
    return list(result.scalars().all())