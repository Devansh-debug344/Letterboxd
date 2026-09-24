"""Tests for the background movie media worker (artwork -> Cloudinary -> DB)."""
import pytest

from app.crud.movie import get_movie_by_omdb_id, save_movie_db
from app.services import movie_import as mi
from app.services.movie_import import MovieImageImportError, enqueue_movie_media, process_movie_media_async

TMDB_PAYLOAD = {
    "imdbID": "123",
    "Title": "Some Film",
    "Year": "2020",
    "Poster": "https://image.tmdb.org/t/p/w342/aaa.jpg",
    "Backdrop": "https://image.tmdb.org/t/p/w780/bbb.jpg",
    "Plot": "A plot.",
    "imdbRating": "7.0",
    "Type": "movie",
}


@pytest.fixture(autouse=True)
def _force_cloudinary_on(monkeypatch):
    monkeypatch.setattr("app.services.movie_import.cloudinary_configured", lambda: True)


async def _fake_download(client, url: str) -> bytes:
    return b"fake-image-bytes"


async def _seed_movie(db, payload=TMDB_PAYLOAD):
    return await save_movie_db(payload, db, backdrop=payload.get("Backdrop"))


def _recording_uploader(monkeypatch):
    calls: list[tuple] = []

    def upload(data, *, folder, public_id, resource_type):
        calls.append((public_id, data))
        return {
            "public_id": f"letterboxd/{folder}/{public_id}",
            "secure_url": f"https://res.cloudinary.com/x/{folder}/{public_id}.jpg",
        }

    monkeypatch.setattr(mi, "_download", _fake_download)
    monkeypatch.setattr(mi, "upload_image", upload)
    return calls


async def test_uploads_artwork_and_is_idempotent(monkeypatch, db):
    movie = await _seed_movie(db)
    calls = _recording_uploader(monkeypatch)

    result = await process_movie_media_async(db, "123", movie.poster, movie.backdrop)
    assert result["status"] == "processed"
    assert set(result["updates"]) == {"poster", "poster_public_id", "backdrop", "backdrop_public_id"}
    assert len(calls) == 2
    assert movie.poster_public_id == "letterboxd/movies/123/poster"
    assert movie.poster == "https://res.cloudinary.com/x/movies/123/poster.jpg"
    assert movie.backdrop_public_id == "letterboxd/movies/123/backdrop"

    again = await process_movie_media_async(db, "123", movie.poster, movie.backdrop)
    assert again["updates"] == []
    assert len(calls) == 2, "processed artwork must not be re-uploaded"


async def test_skips_when_no_artwork_available(monkeypatch, db):
    movie = await _seed_movie(db, {**TMDB_PAYLOAD, "Poster": None})
    calls = _recording_uploader(monkeypatch)

    result = await process_movie_media_async(db, "123", None, None)
    assert result["status"] == "processed"
    assert result["updates"] == []
    assert calls == []
    assert movie.poster is None
    assert movie.poster_public_id is None


async def test_missing_poster_still_processes_backdrop(monkeypatch, db):
    movie = await _seed_movie(db)
    calls = _recording_uploader(monkeypatch)

    result = await process_movie_media_async(db, "123", None, movie.backdrop)
    assert "backdrop_public_id" in result["updates"]
    assert movie.poster_public_id is None
    assert [c[0] for c in calls] == ["123/backdrop"]


async def test_poster_failure_raises_for_retry(monkeypatch, db):
    movie = await _seed_movie(db)
    monkeypatch.setattr(mi, "_download", _fake_download)

    def boom(data, **kwargs):
        raise RuntimeError("cloudinary down")

    monkeypatch.setattr(mi, "upload_image", boom)

    with pytest.raises(MovieImageImportError):
        await process_movie_media_async(db, "123", movie.poster, movie.backdrop)
    await db.refresh(movie)
    assert movie.poster_public_id is None
    assert movie.backdrop_public_id is None


async def test_backdrop_failure_raises_for_retry(monkeypatch, db):
    movie = await _seed_movie(db)
    monkeypatch.setattr(mi, "_download", _fake_download)

    def upload(data, *, folder, public_id, resource_type):
        if public_id.endswith("/backdrop"):
            raise RuntimeError("backdrop upload failed")
        return {
            "public_id": f"letterboxd/{folder}/{public_id}",
            "secure_url": f"https://res.cloudinary.com/x/{folder}/{public_id}.jpg",
        }

    monkeypatch.setattr(mi, "upload_image", upload)

    with pytest.raises(MovieImageImportError):
        await process_movie_media_async(db, "123", movie.poster, movie.backdrop)
    await db.refresh(movie)
    assert movie.poster_public_id == "letterboxd/movies/123/poster"
    assert movie.backdrop_public_id is None


async def test_skips_when_movie_not_saved_yet(db):
    assert await get_movie_by_omdb_id("123", db) is None
    result = await process_movie_media_async(db, "123", "https://img/x.jpg", None)
    assert result["status"] == "skipped"
    assert result["reason"] == "movie not saved yet"


async def test_skips_when_cloudinary_not_configured(monkeypatch, db):
    monkeypatch.setattr("app.services.movie_import.cloudinary_configured", lambda: False)
    await _seed_movie(db)
    result = await process_movie_media_async(db, "123", "https://img/x.jpg", None)
    assert result["status"] == "skipped"
    assert result["reason"] == "cloudinary not configured"


def test_enqueue_movie_media_dispatches(monkeypatch):
    sent: list[dict] = []

    class _Fake:
        @staticmethod
        def delay(**kwargs):
            sent.append(kwargs)

    monkeypatch.setattr("app.tasks.movie_media.process_movie_media_task", _Fake())
    enqueue_movie_media("42", "https://img/p.jpg", None)
    assert sent == [{"imdb_id": "42", "poster_url": "https://img/p.jpg", "backdrop_url": None}]


def test_enqueue_movie_media_swallows_broker_errors(monkeypatch):
    class _Boom:
        @staticmethod
        def delay(**kwargs):
            raise RuntimeError("broker unavailable")

    monkeypatch.setattr("app.tasks.movie_media.process_movie_media_task", _Boom())
    enqueue_movie_media("42", "https://img/p.jpg", None)  # must not raise