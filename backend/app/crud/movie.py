from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.review import Review
from app.models.movie import Movie
from app.models.watched import Watched
from app.models.watchlist import WatchList


async def save_movie_db(
    response: dict,
    db: AsyncSession,
    *,
    poster_public_id: str | None = None,
    backdrop: str | None = None,
    backdrop_public_id: str | None = None,
) -> Movie:
    existing_movie = await get_movie_by_omdb_id(response.get("imdbID"), db)

    if not existing_movie:
        movie = Movie(
            imdb_id=response.get("imdbID"),
            title=response.get("Title"),
            year=response.get("Year"),
            genre=response.get("Genre"),
            poster=response.get("Poster"),
            poster_public_id=poster_public_id,
            backdrop=backdrop,
            backdrop_public_id=backdrop_public_id,
            plot=response.get("Plot"),
            imdbRating=response.get("imdbRating"),
            type=response.get("Type"),
            awards=response.get("Awards"),
            language=response.get("Language"),
            runtime=response.get("Runtime"),
            released=response.get("Released"),
        )
        db.add(movie)
        await db.commit()
        await db.refresh(movie)
        return movie
    return existing_movie


async def get_movie_by_omdb_id(id: str, db: AsyncSession) -> Movie | None:
    result = await db.execute(select(Movie).where(Movie.imdb_id == id))
    return result.scalar_one_or_none()


async def get_movie_by_title(title: str, db: AsyncSession) -> Movie | None:
    result = await db.execute(select(Movie).where(Movie.title == title))
    return result.scalar_one_or_none()


async def get_movie_by_id(id: int, db: AsyncSession) -> Movie | None:
    result = await db.execute(select(Movie).where(Movie.id == id))
    return result.scalar_one_or_none()


async def update_movie_media(movie_id: int, updates: dict[str, str], db: AsyncSession) -> None:
    movie = await db.get(Movie, movie_id)
    if movie is None:
        return
    for key, value in updates.items():
        setattr(movie, key, value)
    await db.commit()


async def get_movie_stats(movie_id: int, db: AsyncSession) -> dict:
    result = await db.execute(
        select(
            select(func.count()).select_from(Review).where(Review.movie_id == movie_id).scalar_subquery(),
            select(func.avg(Review.rating)).where(Review.movie_id == movie_id).scalar_subquery(),
            select(func.count()).select_from(Watched).where(Watched.movie_id == movie_id).scalar_subquery(),
            select(func.count()).select_from(WatchList).where(WatchList.movie_id == movie_id).scalar_subquery(),
        )
    )
    review_count, avg_rating, watched_count, watchlist_count = result.one()

    return {
        "review_count": review_count or 0,
        "avg_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
        "watched_count": watched_count or 0,
        "watchlist_count": watchlist_count or 0,
    }