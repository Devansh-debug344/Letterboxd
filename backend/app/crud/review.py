from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.upsert import insert_ignore
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewOut


async def get_review_by_user_movie(user_id: int, movie_id: int, db: AsyncSession) -> Review | None:
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.movie), selectinload(Review.user))
        .where(Review.user_id == user_id, Review.movie_id == movie_id)
    )
    return result.scalar_one_or_none()


async def get_reviews_by_user(user_id: int, db: AsyncSession, skip: int, limit: int, movie_id: int | None = None) -> list[Review]:
    q = (
        select(Review)
        .options(selectinload(Review.movie), selectinload(Review.user))
        .where(Review.user_id == user_id)
    )
    if movie_id:
        q = q.where(Review.movie_id == movie_id)
    q = q.order_by(Review.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def create_review(user_id: int, movie_id: int, data: ReviewCreate, db: AsyncSession) -> Review:
    statement = insert_ignore(
        db,
        Review,
        "uq_review_user_movie",
        user_id=user_id,
        movie_id=movie_id,
        rating=data.rating,
        review=data.review,
        spoiler=data.spoiler,
    )
    await db.execute(statement)
    await db.commit()
    return await get_review_by_user_movie(user_id, movie_id, db)


async def update_review(user_id: int, movie_id: int, data: ReviewUpdate, db: AsyncSession) -> Review:
    item = await get_review_by_user_movie(user_id, movie_id, db)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if data.rating is not None:
        item.rating = data.rating
    if data.review is not None:
        item.review = data.review
    if data.spoiler is not None:
        item.spoiler = data.spoiler

    await db.commit()
    return await get_review_by_user_movie(user_id, movie_id, db)


async def delete_review(user_id: int, movie_id: int, db: AsyncSession) -> bool:
    item = await get_review_by_user_movie(user_id, movie_id, db)
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True


def to_review_out(item: Review) -> ReviewOut:
    return ReviewOut(
        id=item.id,
        movie_id=item.movie_id,
        user_id=item.user_id,
        movie_name=item.movie.title,
        user_name=item.user.username,
        rating=item.rating,
        review=item.review,
        spoiler=item.spoiler,
        likes=item.likes,
        updated_at=item.updated_at,
    )


async def get_reviews_by_movie(movie_id: int, db: AsyncSession, skip: int, limit: int) -> list[Review]:
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.movie), selectinload(Review.user))
        .where(Review.movie_id == movie_id)
        .order_by(Review.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())