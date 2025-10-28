from .. import db
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum

class Booking(db.Model):
    __tablename__ = "bookings"

    booking_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = db.Column(UUID(as_uuid=True),
                           db.ForeignKey("users.user_id", ondelete="CASCADE"),
                           nullable=False)
    showtime_id = db.Column(UUID(as_uuid=True),
                            db.ForeignKey("showtimes.showtime_id", ondelete="CASCADE"),
                            nullable=False)

    status = db.Column(Enum("PENDING", "CONFIRMED", "CANCELLED", "EXPIRED",
                            name="booking_status_enum", create_type=True),
                       nullable=False, default="PENDING")

    total_cents = db.Column(db.Integer, nullable=False)
    created_at  = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at  = db.Column(db.DateTime(timezone=True), nullable=True)

    __table_args__ = (
        db.CheckConstraint("total_cents >= 0", name="ck_booking_total_nonneg"),
        db.Index("ix_bookings_user_id", "user_id"),
        db.Index("ix_bookings_showtime_id", "showtime_id"),
    )
