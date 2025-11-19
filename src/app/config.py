import os

class Config:
    # Flask / SQLAlchemy
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///dev.db"  # fallback if someone runs without Compose
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    # CORS
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

    # Mail settings
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "1") == "1"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # Frontend URL for links
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # JWT / Cookie Auth
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
    JWT_COOKIE_NAME = os.getenv("JWT_COOKIE_NAME", "access_token")
    JWT_EXPIRES_DAYS = int(os.getenv("JWT_EXPIRES_DAYS", "1"))
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")  # Lax | None | Strict
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "0") == "1"  # True in prod over HTTPS

    # Card Encryption (Fernet key for encrypting payment card data at rest)
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Educational use only - this project handles test data with symmetric encryption
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", None)
