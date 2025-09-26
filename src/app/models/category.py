from .. import db
from .movie_category import movie_categories

class Category(db.Model):
    __tablename__ = "categories"

    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)

    # many-to-many relation back to movies
    movies = db.relationship(
        "Movie",
        secondary=movie_categories,
        back_populates="categories",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Category {self.name}>"
