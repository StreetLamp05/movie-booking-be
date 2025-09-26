from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)


    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", [])}},
         supports_credentials=True)

    # register blueprints under /api/v1
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp, url_prefix="/api/v1")

    # root ping (optional)
    @app.get("/")
    def index():
        return {"status": "ok"}

    return app
