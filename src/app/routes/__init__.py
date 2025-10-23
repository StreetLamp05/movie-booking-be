from flask import Blueprint
from ..models import users
from .. import db


bp = Blueprint("routes", __name__)

from .movie_routes import bp as movie_bp
from .auditorium_routes import bp as auditorium_bp
from .showtime_routes import bp as showtime_bp
from .user_routes import bp as user_bp


bp.register_blueprint(movie_bp)
bp.register_blueprint(auditorium_bp)
bp.register_blueprint(showtime_bp)
bp.register_blueprint(user_bp)


@bp.get("/health")
def health():
    return {"ok": True}

