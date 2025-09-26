from .. import db
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func

class Auditorium(db.Model):
    __tablename__ = "auditoriums"
    __table_args__ = (
        UniqueConstraint("name", name="uq_auditoriums_name"),
    )

    auditorium_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Auditorium {self.name}>"
