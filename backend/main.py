from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

def create_app() -> FastAPI:
    app = FastAPI(title="Movie Booking App", version="1.0.0")
    
    # CORS
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
    
    # Mount static files at root - this should handle JS/CSS files properly
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    
    # First try to serve static files
    @app.middleware("http")
    async def serve_static_or_spa(request, call_next):
        # If it's an API call, let it through normally
        if request.url.path.startswith("/api"):
            return await call_next(request)
            
        # Try to serve static file
        static_file_path = os.path.join(static_dir, request.url.path.lstrip("/"))
        if os.path.isfile(static_file_path):
            return FileResponse(static_file_path)
            
        # If no static file found, serve index.html for SPA routing
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    return app

