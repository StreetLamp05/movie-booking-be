from .. import db
from sqlalchemy.sql import func
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum

class BillingInfo(db.Model):
    __tablename__ = "billing_info"

    billing_info_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = db.Column(UUID(as_uuid=True),
                        db.ForeignKey("users.user_id", ondelete="CASCADE"),
                        nullable=False)

    # Keep existing split fields for now (for backfill); you can drop later if you want.
    first_name = db.Column(db.String(255), nullable=False)
    last_name  = db.Column(db.String(255), nullable=False)

    # NEW per diagram
    cardholder_name = db.Column(db.String(255), nullable=False)
    billing_city    = db.Column(db.String(255), nullable=False)

    card_type = db.Column(Enum("debit", "credit", name="card_type_enum", create_type=False),
                          nullable=False)

    # Encrypted fields: Fernet encryption produces ~88+ char Base64 strings
    card_number = db.Column(db.String(255), nullable=False)  # Was String(16), now encrypted
    card_exp    = db.Column(db.String(255), nullable=False)  # Was String(5), now encrypted
    cardholder_name = db.Column(db.String(255), nullable=False)  # Encryption-safe size

    billing_street   = db.Column(db.String(255), nullable=False)
    billing_state    = db.Column(db.String(2),   nullable=False)
    billing_zip_code = db.Column(db.String(5),   nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        # Removed Luhn check since card_number is now encrypted
    )

    def __repr__(self):
        return f"<BillingInfo {self.billing_info_id} {self.card_type}>"
