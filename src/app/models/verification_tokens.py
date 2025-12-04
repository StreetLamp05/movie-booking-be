from .. import db
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta, timezone
import random

class VerificationToken(db.Model):
    __tablename__ = "verification_tokens"

    token_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(6), nullable=False)  # 6-digit verification code
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    def __init__(self, user_id, token, expires_in_minutes=15):
        self.user_id = user_id
        self.token = token
        self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

    @property
    def is_expired(self):
        return datetime.now(timezone.utc) > self.expires_at
    
    @staticmethod
    def generate_code() -> str:
        """Generate a 6-digit verification code"""
        return str(random.randint(100000, 999999))