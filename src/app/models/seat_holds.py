from .. import db
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID

class SeatHold(db.Model):
    __tablename__ = "seat_holds"

    hold_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id    = db.Column(UUID(as_uuid=True),
                           db.ForeignKey("users.user_id", ondelete="CASCADE"),
                           nullable=False)
    showtime_id = db.Column(UUID(as_uuid=True),
                            db.ForeignKey("showtimes.showtime_id", ondelete="CASCADE"),
                            nullable=False)
    seat_id    = db.Column(db.Integer,
                           db.ForeignKey("seats.seat_id", ondelete="CASCADE"),
                           nullable=False)

    created_at      = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    hold_expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    released_at     = db.Column(db.DateTime(timezone=True), nullable=True)

    __table_args__ = (
        db.Index("ix_seat_holds_showtime_id", "showtime_id"),
        db.Index("ix_seat_holds_user_id", "user_id"),
        # we’ll add a partial unique index in the migration
    )
