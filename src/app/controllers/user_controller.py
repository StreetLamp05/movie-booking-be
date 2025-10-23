import uuid as _uuid
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc, desc
from .. import db
from ..models.users import User


def _bad_request(msg, details=None, code=400):
    return jsonify({"error": {"code": "BAD_REQUEST", "message": msg, "details": details or {}}}), code

def _parse_uuid(s: str):
    try:
        return _uuid.UUID(s)
    except Exception:
        return None


def _user_to_dict(user: User):
    return {
        "user_id": str(user.user_id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_verified": user.is_verified,
        "phone_number": user.phone_number,
        "is_admin": user.is_admin,
        "is_email_list": user.is_email_list,
        "home_street": user.home_street,
        "home_city": user.home_city,
        "home_state": user.home_state,
        "home_country": user.home_country,
        "home_zip_code": user.home_zip_code,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

def create_user():
    '''
    POST /api/v1/users
    body (json): first_name, last_name, email, password_hash, (optional fields)
    '''
    data = request.get_json(silent=True) or {}
    required = ["first_name", "last_name", "email", "password_hash"]
    missing = [k for k in required if not (data.get(k) or "").strip()]
    if missing:
        return _bad_request("Missing required fields", {"missing": missing})

    user = User(
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        email=data["email"].strip().lower(),
        password_hash=data["password_hash"],
        phone_number=data.get("phone_number"),
        is_admin=bool(data.get("is_admin", False)),
        is_email_list=bool(data.get("is_email_list", True)),
        is_verified=bool(data.get("is_verified", False)),
        home_street=data.get("home_street"),
        home_city=data.get("home_city"),
        home_state=data.get("home_state"),
        home_country=data.get("home_country"),
        home_zip_code=data.get("home_zip_code"),
    )

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # unique email
        return jsonify({"error": {"code": "CONFLICT", "message": "Email already exists"}}), 409

    return jsonify(_user_to_dict(user)), 201

def get_user(user_id: str):
    """
    GET /api/v1/users/<user_id>
    """
    uid = _parse_uuid(user_id)
    if not uid:
        return _bad_request("Invalid user_id (must be a UUID).")
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404
    return jsonify(_user_to_dict(user))


def get_users():
    """
    GET /api/v1/users
    Query params:
      q - first/last/email
      limit - default 20 (1..100)
      offset - default 0
      sort - ex: created_at.desc (default), created_at.asc, last_name.asc/desc, first_name.asc/desc
      verified - "true" | "false" (optional)
      admin - "true" | "false" (optional)
    """
    q = (request.args.get("q") or "").strip().lower()
    verified = request.args.get("verified")
    admin = request.args.get("admin")

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
        "last_name.asc": asc(User.last_name),
        "last_name.desc": desc(User.last_name),
        "first_name.asc": asc(User.first_name),
        "first_name.desc": desc(User.first_name),
    }
    order_clause = sort_map.get(sort, desc(User.created_at))

    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                db.func.lower(User.first_name).like(like),
                db.func.lower(User.last_name).like(like),
                db.func.lower(User.email).like(like),
            )
        )
    if verified in {"true", "false"}:
        query = query.filter(User.is_verified.is_(verified == "true"))
    if admin in {"true", "false"}:
        query = query.filter(User.is_admin.is_(admin == "true"))

    total = query.count()
    rows = query.order_by(order_clause).offset(offset).limit(limit).all()

    return jsonify({
        "data": [_user_to_dict(user) for user in rows],
        "page": {"limit": limit, "offset": offset, "total": total}
    })

def edit_user(user_id: str):
    """
    PUT /api/v1/users/<user_id>
    Body: same fields as create; all optional, but at least one must be present.
    """
    uid = _parse_uuid(user_id)
    if not uid:
        return _bad_request("Invalid user_id (must be a UUID).")
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404

    data = request.get_json(silent=True) or {}
    if not data:
        return _bad_request("No fields provided.")

    # keep email unique + normalized
    if "email" in data and data["email"]:
        user.email = data["email"].strip().lower()

    for f in [
        "first_name","last_name","phone_number","password_hash",
        "home_street","home_city","home_state","home_country","home_zip_code"
    ]:
        if f in data:
            setattr(user, f, data.get(f))

    if "is_verified" in data:
        user.is_verified = bool(data["is_verified"])
    if "is_admin" in data:
        user.is_admin = bool(data["is_admin"])
    if "is_email_list" in data:
        user.is_email_list = bool(data["is_email_list"])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": {"code": "CONFLICT", "message": "Email already exists"}}), 409

    return jsonify(_user_to_dict(user))

def delete_user(user_id: str):
    """
    DELETE /api/v1/users/<user_id>
    """
    uid = _parse_uuid(user_id)
    if not uid:
        return _bad_request("Invalid user_id (must be a UUID).")
    user = User.query.filter_by(user_id=uid).first()
    if not user:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404

    db.session.delete(user)
    db.session.commit()
    return ("", 204)