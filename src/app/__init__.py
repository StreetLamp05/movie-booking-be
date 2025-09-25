from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprints
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    # simple root
    @app.get("/")
    def index():
        return {"status": "ok"}

    return app
