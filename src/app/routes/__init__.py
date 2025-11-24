from flask import Blueprint

bp = Blueprint("routes", __name__)

def init_app(app):
    from .movie_routes import bp as movie_bp
    from .auditorium_routes import bp as auditorium_bp
    from .showtime_routes import bp as showtime_bp
    from .user_routes import bp as user_bp
    from .auth_routes import auth_bp
    from .admin_routes import bp as admin_bp
    from .promotions_routes import bp as promotions_bp


    bp.register_blueprint(movie_bp)
    bp.register_blueprint(auditorium_bp)
    bp.register_blueprint(showtime_bp)
    bp.register_blueprint(user_bp)
    bp.register_blueprint(auth_bp, url_prefix='/auth')
    bp.register_blueprint(admin_bp, url_prefix='/admin')
    bp.register_blueprint(promotions_bp, url_prefix='/promo')


    app.register_blueprint(bp, url_prefix="/api/v1")


@bp.get("/health")
def health():
    return {"ok": True}

