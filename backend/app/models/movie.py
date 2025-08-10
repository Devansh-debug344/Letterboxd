from app.db.base import Base
from sqlalchemy import Column , String , Integer, DateTime , Float
from sqlalchemy.orm import relationship
# title, description, genre, release year, image URL
class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    imdb_id = Column(String, unique=True, index=True)
    title = Column(String)
    year = Column(String)
    genre = Column(String)
    poster = Column(String)
    plot = Column(String)
    imdbRating = Column(Float)
    type = Column(String)
    awards = Column(String)
    language = Column(String)
    runtime = Column(String)
    released = Column(String)

    watchlisted_by = relationship("WatchList", back_populates="movie")
    review_by = relationship('Review' , back_populates='movie')