from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

def create_app() -> FastAPI:
    app = FastAPI(title="Movie Booking App", version="1.0.0")

    # CORS
    origins = [
        "*",  # If serving frontend from same server, you can allow all
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Serve static frontend files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    # Your API routers
    from app.api import login, user, watchlist, review
    from app.db.base import Base
    from app.db.session import engine

    Base.metadata.create_all(bind=engine)
    app.include_router(login.router , prefix="/api")
    app.include_router(user.router , prefix="/api")
    app.include_router(watchlist.router , prefix="/api")
    app.include_router(review.router , prefix="/api")

    return app

