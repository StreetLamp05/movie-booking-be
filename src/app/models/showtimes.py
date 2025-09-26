from .. import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Showtime(db.Model):
    __tablename__ = "showtimes"

    # PK: UUID (generated in app; Postgres will store as uuid)
    showtime_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FKs: integers to match your existing tables
    movie_id = db.Column(
        db.Integer,
        db.ForeignKey("movies.movie_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    auditorium_id = db.Column(
        db.Integer,
        db.ForeignKey("auditoriums.auditorium_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Start time (tz-aware)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False)

    # Prices in cents (integers to avoid float issues)
    child_price_cents  = db.Column(db.Integer, nullable=False)
    adult_price_cents  = db.Column(db.Integer, nullable=False)
    senior_price_cents = db.Column(db.Integer, nullable=False)

    # one showtime per auditorium at a given start time
    __table_args__ = (
        db.UniqueConstraint("auditorium_id", "starts_at", name="uq_showtimes_aud_start"),
    )

    def __repr__(self):
        return f"<Showtime {self.showtime_id} movie={self.movie_id} aud={self.auditorium_id}>"
