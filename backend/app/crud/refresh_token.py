from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_token import RefreshToken


async def add_refresh_token_db(user_id: int, hashed_token: str, expires_at: datetime, db: AsyncSession) -> RefreshToken:
    db_token = RefreshToken(
        user_id=user_id,
        token=hashed_token,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def get_token_db(hashed_token: str, db: AsyncSession) -> RefreshToken | None:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == hashed_token))
    return result.scalar_one_or_none()


async def revoke_alltoken_by_id(user_id: int, db: AsyncSession) -> None:
    await db.execute(
        update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
    )
    await db.commit()


async def revoke_token_by_id(user_id: int, db: AsyncSession) -> None:
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
        )
        .values(revoked=True)
    )
    await db.commit()


async def revoke_all_token(db_token: RefreshToken, db: AsyncSession) -> None:
    await db.execute(
        update(RefreshToken).where(RefreshToken.user_id == db_token.user_id).values(revoked=True)
    )
    await db.commit()