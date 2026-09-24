"""Dispatch non-critical auth audit events to the background worker.

Only serializable data is passed to the task; the DB write happens inside the
worker. A failed dispatch must never break login/refresh/logout.
"""
import logging
from fastapi import HTTPException, status
from app.schemas.auth_event import AuthEventSchema

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def log_event(auth_event: AuthEventSchema) -> None:
        try:
            from app.tasks.auth_event import log_auth_event_task

            log_auth_event_task.delay(auth_event.model_dump())
        except Exception:  # noqa: BLE001 - audit logging is never critical
            # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to log auth event {auth_event.event_type} {auth_event.status} ")
            logger.warning(
                "failed to enqueue auth event %s/%s",
                auth_event.event_type,
                auth_event.status,
                exc_info=True,
            )