from .. import db
from sqlalchemy.sql import func
from .movie_category import movie_categories

class Movie(db.Model):
    __tablename__ = "movies"

    movie_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False, index=True)
    cast = db.Column(db.Text)
    director = db.Column(db.Text)
    producer = db.Column(db.Text)
    synopsis = db.Column(db.Text)
    trailer_picture = db.Column(db.Text)  # URL or file path
    video = db.Column(db.Text)            # yt embed url
    film_rating_code = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime(timezone=True), server_default=func.now()
    )

    # many-to-many relation with categories table
    categories = db.relationship(
        "Category",
        secondary=movie_categories,
        back_populates="movies",
        lazy="joined",
    )

    def __repr__(self):
        return f"<Movie {self.title}>"
