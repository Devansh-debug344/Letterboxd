"""Task-level tests: execution, retries, and AuthEvent failure safety."""
import pytest
from celery.exceptions import Retry
from sqlalchemy import select

from app.models.auth_event import AuthEvent
from app.schemas.auth_event import AuthEventSchema
from app.services.auth_event import AuditService
from app.services.movie_import import MovieImageImportError
from app.tasks import auth_event as ae
from app.tasks import movie_media as mt


class FakeRequest:
    def __init__(self, retries: int = 0):
        self.retries = retries


class FakeTask:
    def __init__(self, retries: int = 0):
        self.request = FakeRequest(retries)
        self.calls: list[dict] = []

    def retry(self, *args, **kwargs):
        self.calls.append(kwargs)
        raise Retry()


# --- movie media task --------------------------------------------------------


def test_movie_media_task_executes(monkeypatch):
    async def ok(db, imdb_id, poster_url, backdrop_url):
        return {"status": "processed", "updates": ["poster"]}

    class _Session:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(mt, "process_movie_media_async", ok)
    monkeypatch.setattr(mt, "AsyncSessionLocal", lambda: _Session())

    task = FakeTask()
    result = mt._run_movie_media(task, "42", "https://img/p.jpg", None)
    assert result == {"status": "processed", "updates": ["poster"]}
    assert task.calls == [], "a successful run must not retry"


def test_movie_media_task_retries_on_transient_failure(monkeypatch):
    async def boom(db, imdb_id, poster_url, backdrop_url):
        raise MovieImageImportError("download failed")

    monkeypatch.setattr(mt, "process_movie_media_async", boom)
    task = FakeTask(retries=0)
    with pytest.raises(Retry):
        mt._run_movie_media(task, "42", "https://img/p.jpg", None)
    assert isinstance(task.calls[0]["exc"], MovieImageImportError)
    assert task.calls[0]["countdown"] == 2  # 2 ** retries * 2


def test_movie_media_task_backoff_grows(monkeypatch):
    async def boom(db, imdb_id, poster_url, backdrop_url):
        raise MovieImageImportError("upload failed")

    monkeypatch.setattr(mt, "process_movie_media_async", boom)
    task = FakeTask(retries=4)
    with pytest.raises(Retry):
        mt._run_movie_media(task, "42", "https://img/p.jpg", None)
    assert task.calls[0]["countdown"] == 32  # 2 ** 4 * 2


# --- auth event task ---------------------------------------------------------


async def test_auth_event_task_persists_event(db):
    payload = {
        "event_type": "login",
        "status": "failed",
        "user_id": None,
        "reason": "Wrong password",
        "ip_address": "10.0.0.1",
        "user_agent": "test-agent",
    }
    await ae.log_auth_event_async(db, payload)

    rows = (await db.execute(select(AuthEvent))).scalars().all()
    assert len(rows) == 1
    assert rows[0].event_type == "login"
    assert rows[0].status == "failed"
    assert rows[0].reason == "Wrong password"
    assert rows[0].ip_address == "10.0.0.1"
    assert rows[0].user_agent == "test-agent"


def test_auth_event_task_retries_on_failure(monkeypatch):
    async def boom(db, payload):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(ae, "log_auth_event_async", boom)
    task = FakeTask(retries=1)
    with pytest.raises(Retry):
        ae._run_auth_event(task, {"event_type": "login", "status": "success"})
    assert task.calls[0]["countdown"] == 2  # 2 ** 1


# --- AuditService dispatch ---------------------------------------------------


def test_audit_service_dispatches_serializable_payload(monkeypatch):
    sent: list[dict] = []

    class _Fake:
        @staticmethod
        def delay(payload):
            sent.append(payload)

    monkeypatch.setattr("app.tasks.auth_event.log_auth_event_task", _Fake())

    AuditService.log_event(AuthEventSchema(event_type="login", status="success", user_id=1))
    assert sent == [
        {
            "event_type": "login",
            "status": "success",
            "user_id": 1,
            "reason": None,
            "ip_address": None,
            "user_agent": None,
        }
    ]


def test_audit_service_failure_does_not_raise(monkeypatch):
    class _Boom:
        @staticmethod
        def delay(payload):
            raise RuntimeError("broker unavailable")

    monkeypatch.setattr("app.tasks.auth_event.log_auth_event_task", _Boom())

    AuditService.log_event(AuthEventSchema(event_type="login", status="failed", user_id=None))
    AuditService.log_event(AuthEventSchema(event_type="refresh", status="success", user_id=7))