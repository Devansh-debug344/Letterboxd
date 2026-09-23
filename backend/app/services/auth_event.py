from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth_event import AuthEventSchema
from app.crud.auth_event import add_auth_event_db


class AuditService:
    @staticmethod
    async def log_event(auth_event: AuthEventSchema, db: AsyncSession) -> None:
        await add_auth_event_db(auth_event, db)