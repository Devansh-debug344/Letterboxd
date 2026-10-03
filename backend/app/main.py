from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import login, user, watchlist, review, otp, watched, movie, media
from app.db.session import engine
from app.db.redis import close_redis, init_redis
from app.services.auth_event import AuditService
from app.services.background_dispatch import background_dispatcher
from app.services.fetch_api import close_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    await background_dispatcher.start()
    await AuditService.start()
    try:
        yield
    finally:
        await AuditService.stop()
        await background_dispatcher.stop()
        await close_client()
        await close_redis()
        await engine.dispose()


def create_app():

    app = FastAPI(title="BingeSaga", version="1.0.0", lifespan=lifespan)

    origins = ["https://www.devansh.online"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(login.router, prefix="/api")
    app.include_router(user.router, prefix="/api")
    app.include_router(watchlist.router, prefix="/api")
    app.include_router(review.router, prefix="/api")
    app.include_router(otp.router, prefix="/api")
    app.include_router(watched.router, prefix="/api")
    app.include_router(movie.router, prefix="/api")
    app.include_router(media.router, prefix="/api")

    return app
