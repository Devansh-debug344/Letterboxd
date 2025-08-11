from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.models.user import User 
from app.models.movie import Movie
from app.models.review import Review
from app.models.watchlist import WatchList
from app.api import login , user , watchlist , review
from fastapi.middleware.cors import CORSMiddleware
def create_app() -> FastAPI:
    app = FastAPI(
        title ="Movie Booking App",
        version="1.0.0",
    )
    origins = [
    "http://localhost:5173",      # Vite (React dev server)
    "http://127.0.0.1:5173",
     "https://letterboxd-7.onrender.com", # Sometimes browser switches between 127.0.0.1 and localhost
    ]

    app.add_middleware(
     CORSMiddleware,
     allow_origins=origins,  # 👈 allow frontend dev server
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
    )
    Base.metadata.create_all(bind = engine)
    app.include_router(login.router)
    app.include_router(user.router)
    app.include_router(watchlist.router)
    app.include_router(review.router)
    return app
