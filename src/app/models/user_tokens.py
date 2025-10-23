from .. import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

class UserToken(db.Model):
    __tablename__ = "user_tokens"
    token_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id  = db.Column(UUID(as_uuid=True), db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    purpose  = db.Column(db.String(32), nullable=False)  # "verify_email" | "reset_password"
    token    = db.Column(db.String(255), nullable=False, unique=True)  # signed string
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at    = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
