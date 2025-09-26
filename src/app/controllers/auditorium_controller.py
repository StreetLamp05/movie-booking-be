from flask import request, jsonify
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError
from .. import db
from ..models.auditorium import Auditorium

def _aud_to_dict(a: Auditorium):
    return {
        "id": a.auditorium_id,
        "name": a.name,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }

def _bad_request(msg, details=None):
    return jsonify({"error": {"code": "BAD_REQUEST", "message": msg, "details": details or {}}}), 400

def create_auditorium():
    """
    POST /api/v1/auditorium
    Body: { "name": "Auditorium 1" }
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _bad_request("`name` is required.")

    a = Auditorium(name=name)
    db.session.add(a)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # unique constraint on name
        return jsonify({"error": {"code": "CONFLICT", "message": "Auditorium name already exists"}}), 409

    return jsonify(_aud_to_dict(a)), 201


def get_auditoriums():
    """
    GET /api/v1/auditorium
    Query params:
      q       (str)  - substring match on name
      limit   (int)  - default 20, max 100
      offset  (int)  - default 0
      sort    (str)  - one of: name.asc, name.desc, created_at.asc, created_at.desc (default)
    """
    q = (request.args.get("q") or "").strip()

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
        "name.asc": asc(Auditorium.name),
        "name.desc": desc(Auditorium.name),
        "created_at.asc": asc(Auditorium.created_at),
        "created_at.desc": desc(Auditorium.created_at),
    }
    order_clause = sort_map.get(sort, desc(Auditorium.created_at))

    query = Auditorium.query
    if q:
        query = query.filter(Auditorium.name.ilike(f"%{q}%"))

    total = query.count()
    rows = query.order_by(order_clause).offset(offset).limit(limit).all()

    return jsonify({
        "data": [_aud_to_dict(a) for a in rows],
        "page": {"limit": limit, "offset": offset, "total": total}
    })


def get_auditorium(auditorium_id: int):
    """
    GET /api/v1/auditorium/<auditorium_id>
    """
    a = Auditorium.query.filter_by(auditorium_id=auditorium_id).first()
    if not a:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Auditorium not found"}}), 404
    return jsonify(_aud_to_dict(a))
