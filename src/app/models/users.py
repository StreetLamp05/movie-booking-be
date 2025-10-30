# src/app/models/user.py
from .. import db
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import UniqueConstraint


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
    )

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    first_name = db.Column(db.Text, nullable=False)
    last_name  = db.Column(db.Text, nullable=False)

    email = db.Column(db.Text, nullable=False, index=True, unique=True)
    phone_number = db.Column(db.String(10))
    password_hash = db.Column(db.Text, nullable=False)

    is_admin = db.Column(db.Boolean, default=False)
    is_email_list = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)

    home_street  = db.Column(db.Text)
    home_city    = db.Column(db.Text)
    home_state   = db.Column(db.Text)
    home_country = db.Column(db.Text)
    home_zip_code = db.Column(db.String(9))

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # relationships
    billing_infos = db.relationship(
        "BillingInfo",
        backref="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


    def __repr__(self):
        return f"<User {self.email}>"
