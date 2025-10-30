from .. import db
from sqlalchemy.sql import func

class JWTBlacklist(db.Model):
    __tablename__ = "jwt_blacklist"
    jti = db.Column(db.String(64), primary_key=True)     # JWT ID
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
