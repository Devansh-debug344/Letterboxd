from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Text, Float
from sqlalchemy.orm import relationship
from app.db.base import Base


class Watched(Base):
    __tablename__ = "watched"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id" , ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id" , ondelete="CASCADE"), nullable=False, index=True)
    watched_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="watched_items")
    movie = relationship("Movie", back_populates="watched_items")

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_watched_user_movie"),
    ) #one user can wathced one movie one time 