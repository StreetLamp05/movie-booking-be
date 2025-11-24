from flask import request, jsonify
from sqlalchemy import asc, desc
from werkzeug.security import generate_password_hash
from .. import db
from ..models.users import User
from ..models.billing_info import BillingInfo
from ..services.encryption import CardEncryption
from flask import current_app


def _to_user_row(u: User):
    return {
        "user_id": str(u.user_id),
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "role": "admin" if u.is_admin else "user",
        "is_verified": bool(u.is_verified),
        "phone_number": u.phone_number,
        "home_street": u.home_street,
        "home_city": u.home_city,
        "home_state": u.home_state,
        "home_country": u.home_country,
        "home_zip_code": u.home_zip_code,
        "is_email_list": bool(u.is_email_list),
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


def list_users(_admin_user):
    """GET /api/v1/admin/users?query=&limit=&offset=&sort=created_at.desc"""
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
        "created_at.asc": asc(User.created_at),
        "created_at.desc": desc(User.created_at),
        "email.asc": asc(User.email),
        "email.desc": desc(User.email),
    }
    order_clause = sort_map.get(sort, desc(User.created_at))

    query = User.query
    if q:
        ilike = f"%{q}%"
        query = query.filter(
            db.or_(
                User.email.ilike(ilike),
                User.first_name.ilike(ilike),
                User.last_name.ilike(ilike),
            )
        )
    total = query.count()
    rows = query.order_by(order_clause).offset(offset).limit(limit).all()

    return jsonify(
        {"data": [_to_user_row(u) for u in rows], "page": {"limit": limit, "offset": offset, "total": total}}
    )


def create_user(_admin_user):
    """POST /api/v1/admin/users
    Body: { email, first_name, last_name, password, role?: 'admin'|'user', is_verified?: bool }
    """
    data = request.get_json(silent=True) or {}

    # Validate required fields
    required_fields = ["email", "first_name", "last_name", "password"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": f"{field} is required"}}), 400

    # Check if email already exists
    email = data["email"].strip().lower()
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": {"code": "CONFLICT", "message": "Email already in use"}}), 409

    # Create new user
    new_user = User(
        email=email,
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        password_hash=generate_password_hash(data["password"]),
        is_admin=data.get("role") == "admin",
        is_verified=bool(data.get("is_verified", False))
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"code": "SERVER_ERROR", "message": str(e)}}), 500

    return jsonify(_to_user_row(new_user)), 201


def update_user_admin(_admin_user, user_id):
    """PATCH /api/v1/admin/users/<user_id>
    Body: { role?: 'admin'|'user', is_verified?: bool, email?: string, 
            phone_number?: string, home_street?: string, home_city?: string, 
            home_state?: string, home_country?: string, home_zip_code?: string, is_email_list?: bool }
    (admin can change user properties)
    """
    target = User.query.filter_by(user_id=user_id).first()
    if not target:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404

    data = request.get_json(silent=True) or {}

    # role
    if "role" in data:
        role = data["role"]
        if role not in ("admin", "user"):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "role must be 'admin' or 'user'"}}), 400
        target.is_admin = role == "admin"

    # verification
    if "is_verified" in data:
        target.is_verified = bool(data["is_verified"])

    # email (admin can change)
    if "email" in data:
        new_email = (data["email"] or "").strip().lower()
        if not new_email:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Email cannot be empty"}}), 400
        exists = User.query.filter(User.email == new_email, User.user_id != target.user_id).first()
        if exists:
            return jsonify({"error": {"code": "CONFLICT", "message": "Email already in use"}}), 409
        target.email = new_email

    # phone number
    if "phone_number" in data:
        target.phone_number = (data["phone_number"] or "").strip() or None

    # address fields
    if "home_street" in data:
        target.home_street = (data["home_street"] or "").strip() or None
    if "home_city" in data:
        target.home_city = (data["home_city"] or "").strip() or None
    if "home_state" in data:
        target.home_state = (data["home_state"] or "").strip() or None
    if "home_country" in data:
        target.home_country = (data["home_country"] or "").strip() or None
    if "home_zip_code" in data:
        target.home_zip_code = (data["home_zip_code"] or "").strip() or None

    # promotion subscription
    if "is_email_list" in data:
        target.is_email_list = bool(data["is_email_list"])

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"code": "SERVER_ERROR", "message": str(e)}}), 500

    return jsonify(_to_user_row(target)), 200


def _card_to_admin_dict(card: BillingInfo):
    """Convert BillingInfo for admin view - last 4 digits only"""
    try:
        encryptor = CardEncryption()
        card_number = encryptor.decrypt(card.card_number) if card.card_number else ""
        card_last4 = card_number[-4:] if card_number else "0000"
        cardholder_name = encryptor.decrypt(card.cardholder_name) if card.cardholder_name else ""
        card_exp = encryptor.decrypt(card.card_exp) if card.card_exp else ""
    except Exception as e:
        current_app.logger.warning(f"Failed to decrypt card data: {e}")
        card_last4 = "XXXX"
        cardholder_name = "••••••••"
        card_exp = "••/••"
    
    return {
        "billing_info_id": str(card.billing_info_id),
        "card_type": card.card_type,
        "cardholder_name": cardholder_name,
        "card_last4": card_last4,
        "card_exp": card_exp,
        "billing_address": {
            "street": card.billing_street,
            "city": card.billing_city,
            "state": card.billing_state,
            "zip_code": card.billing_zip_code,
        },
        "created_at": card.created_at.isoformat() if card.created_at else None,
    }


def get_user_cards(_admin_user, user_id):
    """GET /api/v1/admin/users/<user_id>/cards"""
    target = User.query.filter_by(user_id=user_id).first()
    if not target:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404
    
    cards = BillingInfo.query.filter_by(user_id=target.user_id).order_by(BillingInfo.created_at.desc()).all()
    return jsonify([_card_to_admin_dict(c) for c in cards]), 200


def delete_user_card(_admin_user, user_id, card_id):
    """DELETE /api/v1/admin/users/<user_id>/cards/<card_id>"""
    target = User.query.filter_by(user_id=user_id).first()
    if not target:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404
    
    card = BillingInfo.query.filter_by(billing_info_id=card_id, user_id=target.user_id).first()
    if not card:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Card not found"}}), 404
    
    try:
        db.session.delete(card)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"code": "SERVER_ERROR", "message": str(e)}}), 500
    
    return jsonify({"message": "Card deleted"}), 200
