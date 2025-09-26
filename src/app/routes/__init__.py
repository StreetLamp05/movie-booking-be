from flask import Blueprint
from ..models import User
from .. import db



bp = Blueprint("routes", __name__)

from .movie_routes import bp as movie_bp

bp.register_blueprint(movie_bp)


@bp.get("/health")
def health():
    return {"ok": True}

