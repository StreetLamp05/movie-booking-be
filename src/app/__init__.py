from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config
from .services.email_service import mail

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", [])}},
         supports_credentials=True)

    # register blueprints under /api/v1
    from .routes import init_app
    init_app(app)

    # root ping (optional)
    @app.get("/")
    def index():
        return {"status": "ok"}

    return app
