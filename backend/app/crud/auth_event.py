from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Sequence

from app.schemas.auth_event import AuthEventSchema
from app.models.auth_event import AuthEvent


async def add_auth_event_db(auth_event: AuthEventSchema, db: AsyncSession) -> None:
    event = AuthEvent(
        user_id=auth_event.user_id,
        event_type=auth_event.event_type,
        status=auth_event.status,
        reason=auth_event.reason,
        ip_address=auth_event.ip_address,
        user_agent=auth_event.user_agent,
    )
    db.add(event)
    await db.commit()


async def add_auth_events_db(auth_events: Sequence[AuthEventSchema], db: AsyncSession) -> None:
    """Persist a batch of non-critical audit events in one transaction."""
    if not auth_events:
        return
    db.add_all([
        AuthEvent(
            user_id=event.user_id,
            event_type=event.event_type,
            status=event.status,
            reason=event.reason,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
        )
        for event in auth_events
    ])
    await db.commit()
