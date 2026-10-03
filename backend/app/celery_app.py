"""Celery application for background work.

The existing Redis (``REDIS_URL`` from config) is reused as both the broker and
the result backend. Tasks never receive ORM objects or database sessions; they
open their own sessions from ``app.db.session.AsyncSessionLocal``.
"""
from celery import Celery

from app.config import setting

celery_app = Celery(
    "letterboxd",
    broker=setting.CELERY_BROKER_URL or setting.REDIS_URL,
    backend=setting.CELERY_RESULT_BACKEND or setting.REDIS_URL,
    include=["app.tasks.auth_event", "app.tasks.movie_media"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    # Publishing audit events must not keep an HTTP request waiting through
    # broker reconnect attempts. Workers still retry their own broker
    # connections at startup and task execution retries remain unchanged.
    task_publish_retry=False,
    broker_transport_options={
        "socket_connect_timeout": 1,
        "socket_timeout": 1,
        "retry_on_timeout": False,
        "health_check_interval": 30,
        "max_connections": 10,
    },
    worker_prefetch_multiplier=1,
)
