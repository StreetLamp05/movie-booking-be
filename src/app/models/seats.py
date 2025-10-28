from .. import db

class Seat(db.Model):
    __tablename__ = "seats"

    seat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    auditorium_id = db.Column(db.Integer,
                              db.ForeignKey("auditoriums.auditorium_id", ondelete="CASCADE"),
                              nullable=False)

    row_label   = db.Column(db.String(8),  nullable=False)  # e.g. 'A'
    seat_number = db.Column(db.Integer,    nullable=False)  # e.g. 12

    __table_args__ = (
        db.UniqueConstraint("auditorium_id", "row_label", "seat_number",
                            name="uq_seat_in_auditorium"),
        db.Index("ix_seats_auditorium", "auditorium_id"),
    )
