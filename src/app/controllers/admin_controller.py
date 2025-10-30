from flask import request, jsonify
from sqlalchemy import asc, desc
from .. import db
from ..models.users import User


def _to_user_row(u: User):
    return {
        "user_id": str(u.user_id),
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "role": "admin" if u.is_admin else "user",
        "is_verified": bool(u.is_verified),
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


def update_user_admin(_admin_user, user_id):
    """PATCH /api/v1/admin/users/<user_id>
    Body: { role?: 'admin'|'user', is_verified?: bool, email?: string }
    (admin can change another user’s email/role/verification)
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

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"code": "SERVER_ERROR", "message": str(e)}}), 500

    return jsonify(_to_user_row(target)), 200
