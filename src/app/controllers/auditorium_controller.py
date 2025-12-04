from flask import request, jsonify
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError
from .. import db
from ..models.auditorium import Auditorium

def _aud_to_dict(a: Auditorium):
    return {
        "id": a.auditorium_id,
        "auditorium_id": a.auditorium_id,
        "name": a.name,
        "row_count": a.row_count,
        "col_count": a.col_count,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }

def _bad_request(msg, details=None):
    return jsonify({"error": {"code": "BAD_REQUEST", "message": msg, "details": details or {}}}), 400

def create_auditorium():
    """
    POST /api/v1/auditoriums
    Body: { "name": "Auditorium 1", "row_count": 10, "col_count": 10 }
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    row_count = data.get("row_count")
    col_count = data.get("col_count")
    
    if not name:
        return _bad_request("`name` is required.")
    if row_count is None or col_count is None:
        return _bad_request("`row_count` and `col_count` are required.")
    
    try:
        row_count = int(row_count)
        col_count = int(col_count)
    except (ValueError, TypeError):
        return _bad_request("`row_count` and `col_count` must be integers.")
    
    if row_count < 1 or col_count < 1:
        return _bad_request("`row_count` and `col_count` must be positive integers.")

    a = Auditorium(name=name, row_count=row_count, col_count=col_count)
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
    GET /api/v1/auditoriums/<auditorium_id>
    """
    a = Auditorium.query.filter_by(auditorium_id=auditorium_id).first()
    if not a:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Auditorium not found"}}), 404
    return jsonify(_aud_to_dict(a))


def update_auditorium(auditorium_id: int):
    """
    PATCH /api/v1/auditoriums/<auditorium_id>
    Body: { "name": "New Name", "row_count": 12, "col_count": 12 }
    """
    a = Auditorium.query.filter_by(auditorium_id=auditorium_id).first()
    if not a:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Auditorium not found"}}), 404

    data = request.get_json(silent=True) or {}
    
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return _bad_request("`name` cannot be empty.")
        a.name = name
    
    if "row_count" in data:
        row_count = data.get("row_count")
        try:
            row_count = int(row_count)
            if row_count < 1:
                return _bad_request("`row_count` must be a positive integer.")
            a.row_count = row_count
        except (ValueError, TypeError):
            return _bad_request("`row_count` must be an integer.")
    
    if "col_count" in data:
        col_count = data.get("col_count")
        try:
            col_count = int(col_count)
            if col_count < 1:
                return _bad_request("`col_count` must be a positive integer.")
            a.col_count = col_count
        except (ValueError, TypeError):
            return _bad_request("`col_count` must be an integer.")

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": {"code": "CONFLICT", "message": "Auditorium name already exists"}}), 409

    return jsonify(_aud_to_dict(a))


def delete_auditorium(auditorium_id: int):
    """
    DELETE /api/v1/auditoriums/<auditorium_id>
    """
    a = Auditorium.query.filter_by(auditorium_id=auditorium_id).first()
    if not a:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Auditorium not found"}}), 404

    db.session.delete(a)
    db.session.commit()
    
    return jsonify({"message": "Auditorium deleted successfully"}), 200
