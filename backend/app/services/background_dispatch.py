"""Bounded, post-response publishing for non-critical Celery work."""
import asyncio
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from app.config import setting

logger = logging.getLogger(__name__)
Publisher = Callable[[], None]


class BackgroundDispatcher:
    _queue: asyncio.Queue[tuple[str, Publisher]] | None = None
    _workers: list[asyncio.Task] = []
    _executor: ThreadPoolExecutor | None = None

    async def start(self) -> None:
        if self._workers:
            return
        queue_size = max(1, setting.BACKGROUND_DISPATCH_QUEUE_SIZE)
        publisher_count = max(1, setting.BACKGROUND_DISPATCH_PUBLISHERS)
        queue: asyncio.Queue[tuple[str, Publisher]] = asyncio.Queue(maxsize=queue_size)
        executor = ThreadPoolExecutor(max_workers=publisher_count, thread_name_prefix="celery-publisher")
        self._queue = queue
        self._executor = executor
        self._workers = [
            asyncio.create_task(self._consume(queue, executor), name=f"celery-publisher-{index}")
            for index in range(publisher_count)
        ]

    async def stop(self) -> None:
        workers, executor = self._workers, self._executor
        self._workers = []
        self._queue = None
        self._executor = None
        for worker in workers:
            worker.cancel()
        if workers:
            await asyncio.gather(*workers, return_exceptions=True)
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)

    async def _consume(self, queue: asyncio.Queue[tuple[str, Publisher]], executor: ThreadPoolExecutor) -> None:
        loop = asyncio.get_running_loop()
        while True:
            label, publisher = await queue.get()
            try:
                await loop.run_in_executor(executor, self._publish, label, publisher)
            finally:
                queue.task_done()

    def submit(self, label: str, publisher: Publisher) -> None:
        """Queue work without I/O; drop best-effort work when capacity is full."""
        queue = self._queue
        if queue is None:
            # CLI and unit-test callers do not have an ASGI lifespan.
            self._publish(label, publisher)
            return
        try:
            queue.put_nowait((label, publisher))
        except asyncio.QueueFull:
            logger.warning("dropping background dispatch %s because the queue is full", label)

    @staticmethod
    def _publish(label: str, publisher: Publisher) -> None:
        try:
            publisher()
        except Exception:  # noqa: BLE001 - dispatches using this service are best-effort
            logger.warning("failed to enqueue background dispatch %s", label, exc_info=True)


background_dispatcher = BackgroundDispatcher()
