from .. import db
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
import uuid


class Promotion(db.Model):
    __tablename__ = "promotions"

    promotion_id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    code = db.Column(db.Text, nullable=False, unique=True)
    description = db.Column(db.Text)

    # 0–100% (exclusive 0, inclusive 100)
    discount_percent = db.Column(
        db.Numeric(5, 2),
        nullable=False,
    )

    starts_at = db.Column(db.DateTime(timezone=True), nullable=False)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=False)

    # Optional caps
    max_uses = db.Column(db.Integer)
    per_user_limit = db.Column(db.Integer)

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        server_default=text("true"),
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        # discount_percent (0, 100]
        CheckConstraint(
            "discount_percent > 0 AND discount_percent <= 100",
            name="ck_promotions_discount_range",
        ),
        # date range
        CheckConstraint(
            "starts_at < ends_at",
            name="ck_promotions_date_range",
        ),
        # >= 0 || NULL
        CheckConstraint(
            "max_uses IS NULL OR max_uses >= 0",
            name="ck_promotions_max_uses_nonneg",
        ),
        CheckConstraint(
            "per_user_limit IS NULL OR per_user_limit >= 0",
            name="ck_promotions_per_user_nonneg",
        ),
        # indexes
        Index("ix_promotions_code", "code"),
        Index("ix_promotions_validity_window", "starts_at", "ends_at"),
    )
