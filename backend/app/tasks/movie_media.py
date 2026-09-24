"""Background movie media processing: TMDB artwork -> Cloudinary -> database.

Only serializable primitives cross into this task (imdb_id and artwork URLs).
The task opens its own database session from the shared ``AsyncSessionLocal``.
"""
from __future__ import annotations

import asyncio

import httpx

from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.movie_import import MovieImageImportError, process_movie_media_async

logger = get_task_logger(__name__)

TRANSIENT = (MovieImageImportError, httpx.HTTPError)


def _backoff(task) -> int:
    return min(60, 2 ** task.request.retries * 2)


def _run_movie_media(task, imdb_id: str, poster_url=None, backdrop_url=None) -> dict:
    async def _with_session() -> dict:
        async with AsyncSessionLocal() as db:
            return await process_movie_media_async(db, imdb_id, poster_url, backdrop_url)

    try:
        return asyncio.run(_with_session())
    except TRANSIENT as exc:
        # Transient download/upload failures are retried with exponential backoff.
        raise task.retry(exc=exc, countdown=_backoff(task)) from exc


@celery_app.task(bind=True, name="letterboxd.process_movie_media", max_retries=5)
def process_movie_media_task(self, imdb_id: str, poster_url=None, backdrop_url=None) -> dict:
    return _run_movie_media(self, imdb_id, poster_url, backdrop_url)