from .. import db
from sqlalchemy.sql import func
from .movie_category import movie_categories

class Auditorium(db.Model):
    __tablename__ = "auditoriums"

    auditorium_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False, index=True)

    def __repr__(self):
        return f"<Auditorium {self.title}>"
