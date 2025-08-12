from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

def create_app() -> FastAPI:
    app = FastAPI(title="Movie Booking App", version="1.0.0")
    
    # CORS (your existing code is fine)
    origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # API routes FIRST
    from app.api import login, user, watchlist, review
    from app.db.base import Base
    from app.db.session import engine
    Base.metadata.create_all(bind=engine)
    
    app.include_router(login.router, prefix="/api")
    app.include_router(user.router, prefix="/api")
    app.include_router(watchlist.router, prefix="/api")
    app.include_router(review.router, prefix="/api")
    
    # Static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Catch-all for SPA (MUST be last)
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return FileResponse(index_file)  # Always return index.html for SPA
    
    return app

