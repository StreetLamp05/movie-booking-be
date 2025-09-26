from flask import Blueprint
from ..controllers.movie_controller import create_movie, get_movie

bp = Blueprint("movie_routes", __name__, url_prefix="/movies")

@bp.post("")
def create():
    return create_movie()


bp.get("/<int:movie_id>")(get_movie)
