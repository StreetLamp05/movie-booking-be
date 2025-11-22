from flask import Blueprint
from ..controllers.movie_controller import create_movie, get_movie, get_movies, delete_movie, update_movie

bp = Blueprint("movie_routes", __name__, url_prefix="/movies")

# POST /api/v1/movies
@bp.post("")
def create():
    return create_movie()

# GET /api/v1/movies/{movie_id}
bp.get("/<int:movie_id>")(get_movie)

# PUT /api/v1/movies/{movie_id}
@bp.put("/<int:movie_id>")
def update(movie_id):
    return update_movie(movie_id)

# DELETE /api/v1/movies/{movie_id}
@bp.delete("/<int:movie_id>")
def delete(movie_id):
    return delete_movie(movie_id)

# GET /api/v1/movies
bp.get("")(get_movies)