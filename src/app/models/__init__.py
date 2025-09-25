from .. import db
from .movie import Movie
from .category import Category
from .movie_category import movie_categories

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
