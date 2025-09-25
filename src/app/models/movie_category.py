from .. import db

# association table for movies <-> categories
movie_categories = db.Table(
    "movie_categories",
    db.Column(
        "movie_id",
        db.Integer,
        db.ForeignKey("movies.movie_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "category_id",
        db.Integer,
        db.ForeignKey("categories.category_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
