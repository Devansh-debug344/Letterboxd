"""Batch and dispatch non-critical auth audit events without blocking auth.

Only serializable data is passed to the task; the DB write happens inside the
worker. A failed dispatch must never break login/refresh/logout.
"""
import asyncio
import logging

from app.config import setting
from app.services.background_dispatch import background_dispatcher
from app.schemas.auth_event import AuthEventSchema

logger = logging.getLogger(__name__)


class AuditService:
    _queue: asyncio.Queue[dict] | None = None
    _worker: asyncio.Task | None = None

    @classmethod
    async def start(cls) -> None:
        if cls._worker is not None:
            return
        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=max(1, setting.AUDIT_EVENT_QUEUE_SIZE))
        cls._queue = queue
        cls._worker = asyncio.create_task(cls._consume(queue), name="audit-batcher")

    @classmethod
    async def stop(cls) -> None:
        worker = cls._worker
        cls._worker = None
        cls._queue = None
        if worker is not None:
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)

    @classmethod
    async def _consume(cls, queue: asyncio.Queue[dict]) -> None:
        batch_size = max(1, setting.AUDIT_EVENT_BATCH_SIZE)
        wait_seconds = max(0, setting.AUDIT_EVENT_BATCH_WAIT_MS) / 1000
        while True:
            batch = [await queue.get()]
            try:
                deadline = asyncio.get_running_loop().time() + wait_seconds
                while len(batch) < batch_size:
                    remaining = deadline - asyncio.get_running_loop().time()
                    if remaining <= 0:
                        break
                    try:
                        batch.append(await asyncio.wait_for(queue.get(), timeout=remaining))
                    except asyncio.TimeoutError:
                        break
                background_dispatcher.submit(
                    f"auth-event-batch:{len(batch)}",
                    lambda payloads=tuple(batch): cls._publish_batch(list(payloads)),
                )
            finally:
                for _ in batch:
                    queue.task_done()

    @staticmethod
    def _publish_batch(payloads: list[dict]) -> None:
        from app.tasks.auth_event import log_auth_event_task

        log_auth_event_task.delay(payloads)

    @classmethod
    def log_event(cls, auth_event: AuthEventSchema) -> None:
        """Queue an event in O(1), or drop it when the bounded queue is full."""
        payload = auth_event.model_dump()
        queue = cls._queue
        if queue is None:
            background_dispatcher.submit("auth-event-batch:1", lambda: cls._publish_batch([payload]))
            return
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            logger.warning("dropping auth event because the audit queue is full")
