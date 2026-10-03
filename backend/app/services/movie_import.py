"""Movie artwork processing, executed by the Celery worker.

The HTTP request path stores movie metadata (with the original TMDB artwork
URLs) and returns immediately. A background task later downloads the poster and
backdrop, uploads them to Cloudinary and updates the movie record with the
Cloudinary references. Nothing here blocks a request.
"""
from __future__ import annotations

import asyncio
import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.movie import get_movie_by_omdb_id, update_movie_media
from app.services.background_dispatch import background_dispatcher
from app.services.cache import invalidate
from app.services.cloudinary_service import cloudinary_configured, upload_image

logger = logging.getLogger(__name__)

_IMAGE_MAX_BYTES = 10 * 1024 * 1024
_IMAGE_TIMEOUT = httpx.Timeout(8.0, connect=3.0)


class MovieImageImportError(Exception):
    """Raised when an artwork download/upload fails (transient -> retried)."""


def _public_id(imdb_id: str, kind: str) -> str:
    # Idempotent asset path: re-uploading the same kind reuses the public id,
    # which the Cloudinary SDK overwrites instead of creating a duplicate.
    return f"{imdb_id}/{kind}"


async def _download(client: httpx.AsyncClient, url: str) -> bytes:
    response = await client.get(url)
    response.raise_for_status()
    data = await response.aread()
    if len(data) > _IMAGE_MAX_BYTES:
        raise MovieImageImportError("Image file is too large")
    return data


async def _upload_artwork(client: httpx.AsyncClient, imdb_id: str, kind: str, source_url: str) -> dict:
    data = await _download(client, source_url)
    try:
        return await asyncio.to_thread(
            upload_image,
            data,
            folder="movies",
            public_id=_public_id(imdb_id, kind),
            resource_type="image",
        )
    except Exception as exc:  # noqa: BLE001 - surface any SDK failure for retry
        raise MovieImageImportError(f"{kind} upload to Cloudinary failed") from exc


async def process_movie_media_async(
    db: AsyncSession,
    imdb_id: str,
    poster_url: str | None,
    backdrop_url: str | None,
) -> dict:
    """Upload artwork for an already-saved movie and store the Cloudinary refs.

    Idempotent: artwork already processed (``*_public_id`` present) is skipped,
    so task redelivery or duplicates never re-upload assets. Failures raise
    :class:`MovieImageImportError` (or httpx errors) so the task can retry.
    """
    if not imdb_id:
        return {"status": "skipped", "reason": "missing imdb_id"}

    if not cloudinary_configured():
        logger.warning("Cloudinary not configured; skipping media processing for %s", imdb_id)
        return {"status": "skipped", "reason": "cloudinary not configured"}

    movie = await get_movie_by_omdb_id(imdb_id, db)
    if movie is None:
        return {"status": "skipped", "reason": "movie not saved yet"}

    updated: list[str] = []
    async with httpx.AsyncClient(timeout=_IMAGE_TIMEOUT, http2=True, follow_redirects=True) as client:
        if poster_url and poster_url != "N/A" and movie.poster_public_id is None:
            asset = await _upload_artwork(client, imdb_id, "poster", poster_url)
            await update_movie_media(
                movie.id,
                {"poster": asset.get("secure_url"), "poster_public_id": asset.get("public_id")},
                db,
            )
            updated.append("poster")
            updated.append("poster_public_id")
        if backdrop_url and backdrop_url != "N/A" and movie.backdrop_public_id is None:
            asset = await _upload_artwork(client, imdb_id, "backdrop", backdrop_url)
            await update_movie_media(
                movie.id,
                {"backdrop": asset.get("secure_url"), "backdrop_public_id": asset.get("public_id")},
                db,
            )
            updated.append("backdrop")
            updated.append("backdrop_public_id")

    if updated:
        await invalidate(f"movie:{imdb_id}")

    return {"status": "processed", "imdb_id": imdb_id, "updates": updated}


def enqueue_movie_media(imdb_id: str, poster_url: str | None, backdrop_url: str | None) -> None:
    """Queue media processing without synchronously publishing to Celery."""
    if not imdb_id:
        return

    def publish() -> None:
        from app.tasks.movie_media import process_movie_media_task

        process_movie_media_task.delay(imdb_id=imdb_id, poster_url=poster_url, backdrop_url=backdrop_url)

    background_dispatcher.submit(f"movie-media:{imdb_id}", publish)
