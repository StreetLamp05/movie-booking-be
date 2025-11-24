from flask import request, jsonify
from sqlalchemy import asc, desc
from .. import db
from ..models.promotions import Promotion
from ..models.users import User
from ..services.email_service import send_promotion_emails_bulk
from datetime import datetime


def _to_promotion_row(p: Promotion):
    """Convert Promotion to JSON-serializable dict"""
    return {
        "promotion_id": str(p.promotion_id),
        "code": p.code,
        "description": p.description,
        "discount_percent": float(p.discount_percent),
        "starts_at": p.starts_at.isoformat() if p.starts_at else None,
        "ends_at": p.ends_at.isoformat() if p.ends_at else None,
        "max_uses": p.max_uses,
        "per_user_limit": p.per_user_limit,
        "is_active": bool(p.is_active),
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def list_promotions(_admin_user):
    """GET /api/v1/admin/promotions?query=&limit=&offset=&sort=created_at.desc"""
    q = (request.args.get("query") or "").strip()
    try:
        limit = min(max(int(request.args.get("limit", 20)), 1), 100)
    except ValueError:
        limit = 20
    try:
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        offset = 0
    sort = (request.args.get("sort") or "created_at.desc").lower()
    sort_map = {
        "created_at.asc": asc(Promotion.created_at),
        "created_at.desc": desc(Promotion.created_at),
        "code.asc": asc(Promotion.code),
        "code.desc": desc(Promotion.code),
        "discount_percent.asc": asc(Promotion.discount_percent),
        "discount_percent.desc": desc(Promotion.discount_percent),
    }
    order_clause = sort_map.get(sort, desc(Promotion.created_at))

    query = Promotion.query
    if q:
        ilike = f"%{q}%"
        query = query.filter(
            db.or_(
                Promotion.code.ilike(ilike),
                Promotion.description.ilike(ilike),
            )
        )
    total = query.count()
    rows = query.order_by(order_clause).offset(offset).limit(limit).all()

    return jsonify(
        {"data": [_to_promotion_row(p) for p in rows], "page": {"limit": limit, "offset": offset, "total": total}}
    )


def create_promotion(_admin_user):
    """POST /api/v1/admin/promotions
    Body: { code, description?, discount_percent, starts_at, ends_at, max_uses?, per_user_limit?, is_active? }
    """
    data = request.get_json(silent=True) or {}

    # Validate required fields
    required_fields = ["code", "discount_percent", "starts_at", "ends_at"]
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": f"{field} is required"}}), 400

    # Check if code already exists
    code = data["code"].strip().upper()
    existing = Promotion.query.filter_by(code=code).first()
    if existing:
        return jsonify({"error": {"code": "CONFLICT", "message": "Promotion code already exists"}}), 409

    # Validate discount percent
    try:
        discount = float(data["discount_percent"])
        if discount <= 0 or discount > 100:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Discount must be between 0 and 100"}}), 400
    except (ValueError, TypeError):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid discount_percent"}}), 400

    # Parse dates
    try:
        starts_at = datetime.fromisoformat(data["starts_at"].replace('Z', '+00:00'))
        ends_at = datetime.fromisoformat(data["ends_at"].replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid date format"}}), 400

    if starts_at >= ends_at:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Start date must be before end date"}}), 400

    # Create promotion
    new_promotion = Promotion(
        code=code,
        description=(data.get("description") or "").strip() or None,
        discount_percent=discount,
        starts_at=starts_at,
        ends_at=ends_at,
        max_uses=data.get("max_uses"),
        per_user_limit=data.get("per_user_limit"),
        is_active=bool(data.get("is_active", True))
    )

    try:
        db.session.add(new_promotion)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"code": "SERVER_ERROR", "message": str(e)}}), 500

    return jsonify(_to_promotion_row(new_promotion)), 201


def update_promotion(_admin_user, promotion_id):
    """PATCH /api/v1/admin/promotions/<promotion_id>
    Body: { code?, description?, discount_percent?, starts_at?, ends_at?, max_uses?, per_user_limit?, is_active? }
    """
    promotion = Promotion.query.filter_by(promotion_id=promotion_id).first()
    if not promotion:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Promotion not found"}}), 404

    data = request.get_json(silent=True) or {}

    # Update code
    if "code" in data:
        code = data["code"].strip().upper()
        existing = Promotion.query.filter(
            Promotion.code == code, Promotion.promotion_id != promotion.promotion_id
        ).first()
        if existing:
            return jsonify({"error": {"code": "CONFLICT", "message": "Promotion code already exists"}}), 409
        promotion.code = code

    # Update description
    if "description" in data:
        promotion.description = (data["description"] or "").strip() or None

    # Update discount
    if "discount_percent" in data:
        try:
            discount = float(data["discount_percent"])
            if discount <= 0 or discount > 100:
                return jsonify({"error": {"code": "BAD_REQUEST", "message": "Discount must be between 0 and 100"}}), 400
            promotion.discount_percent = discount
        except (ValueError, TypeError):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid discount_percent"}}), 400

    # Update dates
    if "starts_at" in data:
        try:
            promotion.starts_at = datetime.fromisoformat(data["starts_at"].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid starts_at format"}}), 400

    if "ends_at" in data:
        try:
            promotion.ends_at = datetime.fromisoformat(data["ends_at"].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid ends_at format"}}), 400

    # Validate date range
    if promotion.starts_at >= promotion.ends_at:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Start date must be before end date"}}), 400

    # Update limits
    if "max_uses" in data:
        promotion.max_uses = data["max_uses"]
    if "per_user_limit" in data:
        promotion.per_user_limit = data["per_user_limit"]

    # Update status
    if "is_active" in data:
        promotion.is_active = bool(data["is_active"])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"code": "SERVER_ERROR", "message": str(e)}}), 500

    return jsonify(_to_promotion_row(promotion)), 200


def delete_promotion(_admin_user, promotion_id):
    """DELETE /api/v1/admin/promotions/<promotion_id>"""
    promotion = Promotion.query.filter_by(promotion_id=promotion_id).first()
    if not promotion:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Promotion not found"}}), 404

    try:
        db.session.delete(promotion)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"code": "SERVER_ERROR", "message": str(e)}}), 500

    return jsonify({"message": "Promotion deleted"}), 200


def send_promotion_emails(_admin_user, promotion_id):
    """POST /api/v1/admin/promotions/<promotion_id>/send-email
    Send promotion email to all subscribers (users with is_email_list=True)
    """
    promotion = Promotion.query.filter_by(promotion_id=promotion_id).first()
    if not promotion:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Promotion not found"}}), 404

    # Query all subscribed users
    subscribed_users = User.query.filter_by(is_email_list=True).all()
    if not subscribed_users:
        return jsonify({"message": "No subscribed users found", "emails_sent": 0, "errors": []}), 200

    # Prepare email parameters
    emails = [user.email for user in subscribed_users]
    start_date = promotion.starts_at.isoformat() if promotion.starts_at else None
    end_date = promotion.ends_at.isoformat() if promotion.ends_at else None

    # Send emails in bulk
    try:
        send_promotion_emails_bulk(emails, promotion.code, float(promotion.discount_percent), start_date, end_date, promotion.description)
        return jsonify({
            "message": "Promotion emails sent",
            "emails_sent": len(emails),
            "errors": [],
        }), 200
    except Exception as e:
        return jsonify({"error": {"code": "SERVER_ERROR", "message": str(e)}}), 500
