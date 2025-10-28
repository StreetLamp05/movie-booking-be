from .. import db
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Review(db.Model):
    __tablename__ = "reviews"

    review_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id   = db.Column(UUID(as_uuid=True),
                          db.ForeignKey("users.user_id", ondelete="CASCADE"),
                          nullable=False)
    movie_id  = db.Column(db.Integer,
                          db.ForeignKey("movies.movie_id", ondelete="CASCADE"),
                          nullable=False)

    rating  = db.Column(db.Integer, nullable=False)  # 1..5
    comment = db.Column(db.Text)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    # helpful indexes
    __table_args__ = (
        db.Index("ix_reviews_movie_id", "movie_id"),
        db.Index("ix_reviews_user_id", "user_id"),
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
    )
