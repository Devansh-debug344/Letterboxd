from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.api import login, user, watchlist, review, otp , watched , movie
from app.db.base import Base  
from app.db.session import engine
from sqlalchemy.exc import OperationalError


def create_app():

    app = FastAPI(title="LetterBoxd", version="1.0.0")
    
    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    
    # @app.on_event("startup")
    # async def startup_db():
    #     try:
    #         Base.metadata.create_all(bind=engine)
    #         print("Database connected and tables created")
    #     except OperationalError as e:
    #         print("Database not ready yet:", e)
    
    app.include_router(login.router, prefix="/api")
    app.include_router(user.router, prefix="/api")
    app.include_router(watchlist.router, prefix="/api") 
    app.include_router(review.router, prefix="/api")
    app.include_router(otp.router , prefix="/api")
    app.include_router(watched.router , prefix="/api")
    app.include_router(movie.router , prefix="/api")

    
    # static_dir = os.path.join(os.path.dirname(__file__), "static")
    
    # @app.middleware("http")
    # async def serve_static_or_spa(request, call_next):
    #     if request.url.path.startswith("/api"):
    #         return await call_next(request)
    #     static_file_path = os.path.join(static_dir, request.url.path.lstrip("/"))
    #     if os.path.isfile(static_file_path):
    #         return FileResponse(static_file_path)
    #     return FileResponse(os.path.join(static_dir, "index.html"))
    
    return app
