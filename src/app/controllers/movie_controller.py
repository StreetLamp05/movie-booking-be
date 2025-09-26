from flask import request, jsonify
from .. import db
from ..models.movie import Movie
from ..models.category import Category

# helper

MOVIE_FIELDS = [
    "title", "cast", "director", "producer", "synopsis",
    "trailer_picture", "video", "film_rating_code"
]

def _movie_to_dict(m: Movie):
    return {
        "id": m.movie_id,
        "title": m.title,
        "cast": m.cast,
        "director": m.director,
        "producer": m.producer,
        "synopsis": m.synopsis,
        "trailer_picture": m.trailer_picture,
        "video": m.video,
        "film_rating_code": m.film_rating_code,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "categories": [{"id": c.category_id, "name": c.name} for c in (m.categories or [])],
    }

def _bad_request(message, details=None):
    return jsonify({"error": {"code": "BAD_REQUEST", "message": message, "details": details or {}}}), 400

# controllers



def get_movie(movie_id):
    """GET /api/v1/movies/<movie_id>"""
    movie = db.session.get(Movie, movie_id)
    if not movie:
        return jsonify({"error": {"code": "NOT_FOUND", "message": f"Movie {movie_id} not found"}}), 404
    return jsonify(_movie_to_dict(movie)), 200



def create_movie():
    """
    POST /api/v1/movies
    Body:
    {
      "title": "Inception",
      "cast": "...",
      "director": "...",
      "producer": "...",
      "synopsis": "...",
      "trailer_picture": "https://.../cover.jpg",
      "video": "https://.../movie.mp4",
      "film_rating_code": "PG-13",
      "categories": ["Sci-Fi", "Thriller"]          # optional
      # or categories_ids: [1, 2]                   # optional
    }
    """


    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return _bad_request("`title` is required.")

    # create movie object
    movie = Movie()
    for f in MOVIE_FIELDS:
        if f in data:
            setattr(movie, f, data.get(f))

    # resolve categories by name/   ids
    categories = []

    # names
    cat_names = data.get("categories") or []
    if not isinstance(cat_names, list):
        return _bad_request("`categories` must be a list of names if provided.")

    for name in cat_names:
        if not isinstance(name, str) or not name.strip():
            return _bad_request("Every category name must be a non-empty string.")
        name = name.strip()
        cat = Category.query.filter_by(name=name).first()
        if not cat:
            cat = Category(name=name)
            db.session.add(cat)
        categories.append(cat)

    # ids (optional)
    cat_ids = data.get("categories_ids") or []
    if cat_ids:
        if not isinstance(cat_ids, list):
            return _bad_request("`categories_ids` must be a list of integers if provided.")
        by_id = Category.query.filter(Category.category_id.in_(cat_ids)).all()
        found_ids = {c.category_id for c in by_id}
        missing = [cid for cid in cat_ids if cid not in found_ids]
        if missing:
            return _bad_request("Some category ids do not exist.", {"missing_ids": missing})
        categories.extend(by_id)

    # ensure uniqueness of categories
    if categories:
        seen = {}
        unique = []
        for c in categories:
            if c.name not in seen:
                seen[c.name] = True
                unique.append(c)
        movie.categories = unique

    db.session.add(movie)
    db.session.commit()
    return jsonify(_movie_to_dict(movie)), 201
