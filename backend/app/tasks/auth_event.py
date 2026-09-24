"""Background persistence of (non-critical) authentication audit events.

The login/refresh/logout request path only enqueues a serializable event dict;
this task writes it to the database with its own session. AuthEvent failures are
logged and retried briefly, but never affect authentication itself.
"""
from __future__ import annotations

import asyncio

from celery.utils.log import get_task_logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.crud.auth_event import add_auth_event_db
from app.db.session import AsyncSessionLocal
from app.schemas.auth_event import AuthEventSchema

logger = get_task_logger(__name__)


async def log_auth_event_async(db: AsyncSession, payload: dict) -> None:
    """Persist one serializable auth event using an existing session."""
    await add_auth_event_db(AuthEventSchema(**payload), db)


def _backoff(task) -> int:
    return min(30, 2 ** task.request.retries)


def _run_auth_event(task, payload: dict) -> None:
    async def _with_session() -> None:
        async with AsyncSessionLocal() as db:
            await log_auth_event_async(db, payload)

    try:
        asyncio.run(_with_session())
    except Exception as exc:  # noqa: BLE001 - audit logging is best effort
        logger.warning("auth event persistence failed; retrying", exc_info=True)
        raise task.retry(exc=exc, countdown=_backoff(task)) from exc


@celery_app.task(bind=True, name="letterboxd.log_auth_event", max_retries=3)
def log_auth_event_task(self, auth_event: dict) -> None:
    return _run_auth_event(self, auth_event)