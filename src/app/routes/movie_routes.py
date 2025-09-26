from flask import Blueprint
from ..controllers.movie_controller import create_movie, get_movie, get_movies

bp = Blueprint("movie_routes", __name__, url_prefix="/movies")

# POST /api/v1/movies
@bp.post("")
def create():
    return create_movie()

# GET /api/v1/movies/{movie_id}
bp.get("/<int:movie_id>")(get_movie)

# GET /api/v1/movies
bp.get("")(get_movies)