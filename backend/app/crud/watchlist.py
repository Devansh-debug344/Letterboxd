from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.upsert import insert_ignore
from app.models.watchlist import WatchList
from app.models.movie import Movie


async def create_save_movie(movie_id: int, user_id: int, db: AsyncSession) -> WatchList | None:
    statement = insert_ignore(
        db,
        WatchList,
        "uq_watchlist_user_movie",
        user_id=user_id,
        movie_id=movie_id,
    )
    await db.execute(statement)
    await db.commit()
    result = await db.execute(
        select(WatchList).where(
            WatchList.movie_id == movie_id,
            WatchList.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_save_movie(movie: object, watchlist: WatchList, db: AsyncSession) -> WatchList:
    for key, value in movie.model_dump(exclude_unset=True).items():
        setattr(watchlist, key, value)
    await db.commit()
    await db.refresh(watchlist)
    return watchlist


async def get_save_movie(user_id: int, db: AsyncSession) -> list[WatchList]:
    result = await db.execute(select(WatchList).where(WatchList.user_id == user_id))
    return list(result.scalars().all())


async def get_watchlist_with_movies(user_id: int, db: AsyncSession):
    result = await db.execute(
        select(WatchList, Movie)
        .join(Movie, Movie.id == WatchList.movie_id)
        .where(WatchList.user_id == user_id)
        .order_by(WatchList.created_at.desc())
    )
    return result.all()


async def del_save_movie_by_movie_id(movie_id: int, user_id: int, db: AsyncSession) -> bool:
    result = await db.execute(
        select(WatchList).where(
            WatchList.user_id == user_id,
            WatchList.movie_id == movie_id,
        )
    )
    movie_deleted = result.scalar_one_or_none()

    if not movie_deleted:
        return False
    await db.delete(movie_deleted)
    await db.commit()
    return True