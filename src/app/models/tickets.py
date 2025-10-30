from .. import db
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Ticket(db.Model):
    __tablename__ = "tickets"

    ticket_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    booking_id  = db.Column(UUID(as_uuid=True),
                            db.ForeignKey("bookings.booking_id", ondelete="CASCADE"),
                            nullable=False)
    showtime_id = db.Column(UUID(as_uuid=True),
                            db.ForeignKey("showtimes.showtime_id", ondelete="CASCADE"),
                            nullable=False)
    seat_id     = db.Column(db.Integer,
                            db.ForeignKey("seats.seat_id", ondelete="CASCADE"),
                            nullable=False)

    price_cents = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("booking_id", "seat_id", name="uq_ticket_per_seat_in_booking"),
        db.CheckConstraint("price_cents >= 0", name="ck_ticket_price_nonneg"),
        db.Index("ix_tickets_showtime_id", "showtime_id"),
        db.Index("ix_tickets_seat_id", "seat_id"),
    )
