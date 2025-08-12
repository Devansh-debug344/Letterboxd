from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.db.base import Base
from app.db.session import engine
from app.models.user import User 
from app.models.movie import Movie
from app.models.review import Review
from app.models.watchlist import WatchList
from app.api import login, user, watchlist, review
from fastapi.middleware.cors import CORSMiddleware
import os

def create_app() -> FastAPI:
    app = FastAPI(
        title="Movie Booking App",
        version="1.0.0",
    )

    # Enable CORS in dev only
    if os.getenv("ENV", "dev") == "dev":
        origins = [
            "http://localhost:5173",  # Vite (React dev server)
            "http://127.0.0.1:5173",
        ]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # DB tables creation
    Base.metadata.create_all(bind=engine)

    # Include API routes
    app.include_router(login.router)
    app.include_router(user.router)
    app.include_router(watchlist.router)
    app.include_router(review.router)

    # Serve static frontend files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Catch-all route to serve index.html (for React Router)
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        index_path = os.path.join("static", "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "index.html not found"}

    return app


app = create_app()
