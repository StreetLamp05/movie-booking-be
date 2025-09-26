from .. import db
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import CheckConstraint, Enum


class BillingInfo(db.Model):
    __tablename__ = "billing_info"

    billing_info_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)

    card_type = db.Column(
        Enum("debit", "credit", name="card_type_enum", create_type=True),
        nullable=False
    )

    card_number = db.Column(
        db.String(16),
        nullable=False
    )

    card_exp = db.Column(db.String(5), nullable=False)  # e.g. "12/28"

    billing_street = db.Column(db.Text, nullable=False)
    billing_state = db.Column(db.Text, nullable=False)
    billing_zip_code = db.Column(db.String(9), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # enforce card_number = 16 digits
        CheckConstraint("card_number ~ '^[0-9]{16}$'", name="ck_card_number_digits"),
    )

    def __repr__(self):
        return f"<BillingInfo {self.billing_info_id} {self.card_type}>"
