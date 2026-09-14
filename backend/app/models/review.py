from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Float,
    ForeignKey,
    Text,
    Boolean,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id" , ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Float, nullable=False)          # 0.5–5
    review = Column(Text, nullable=True)            # text optional, rating required
    spoiler = Column(Boolean, default=False, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="review")
    movie = relationship("Movie", back_populates="review")

    __table_args__ = (
    UniqueConstraint("user_id", "movie_id", name="uq_review_user_movie"),
 ) #CANNOT REVIEW THE SAME MOVIE TWICE


    # ondelete="CASCADE"

    # This configuration tells the database to create a literal ON DELETE CASCADE constraint on the table's foreign key column schema.
    # Delete Parent: When a parent row is deleted, the database automatically wipes out all rows in the child table that reference that parent's ID

