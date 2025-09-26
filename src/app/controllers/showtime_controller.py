from flask import request, jsonify
from sqlalchemy import asc, desc, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from .. import db
from ..models.showtimes import Showtime
from ..models.movie import Movie
from ..models.auditorium import Auditorium

# helpers
def _bad_request(msg, details=None, code=400):
    return jsonify({"error": {"code": "BAD_REQUEST", "message": msg, "details": details or {}}}), code

def _parse_dt(v: str):
    # "2025-10-01T19:30:00Z"
    try:
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        return datetime.fromisoformat(v)
    except Exception:
        return None

def _to_dict(s: Showtime):
    return {
        "showtime_id": str(s.showtime_id),
        "movie_id": s.movie_id,
        "auditorium_id": s.auditorium_id,
        "starts_at": s.starts_at.isoformat() if s.starts_at else None,
        "child_price_cents": s.child_price_cents,
        "adult_price_cents": s.adult_price_cents,
        "senior_price_cents": s.senior_price_cents,
    }

# controllers
def create_showtime():
    """
    POST /api/v1/showtimes
    Body:
    {
      "movie_id": 1,
      "auditorium_id": 2,
      "starts_at": "2025-10-01T19:30:00Z",
      "child_price_cents": 900,
      "adult_price_cents": 1400,
      "senior_price_cents": 1100
    }
    """
    data = request.get_json(silent=True) or {}

    # req fields
    try:
        movie_id = int(data.get("movie_id"))
        auditorium_id = int(data.get("auditorium_id"))
    except Exception:
        return _bad_request("`movie_id` and `auditorium_id` must be integers.")

    starts_at_raw = data.get("starts_at")
    starts_at = _parse_dt(starts_at_raw) if isinstance(starts_at_raw, str) else None
    if not starts_at:
        return _bad_request("`starts_at` must be an ISO datetime string (e.g. 2025-10-01T19:30:00Z).")

    # price
    try:
        child = int(data.get("child_price_cents"))
        adult = int(data.get("adult_price_cents"))
        senior = int(data.get("senior_price_cents"))
    except Exception:
        return _bad_request("Price fields must be integers (cents).")

    if min(child, adult, senior) < 0:
        return _bad_request("Price fields must be non-negative integers (cents).")

    # check FK exists
    if not Movie.query.filter_by(movie_id=movie_id).first():
        return _bad_request("movie_id does not exist.", code=404)
    if not Auditorium.query.filter_by(auditorium_id=auditorium_id).first():
        return _bad_request("auditorium_id does not exist.", code=404)

    s = Showtime(
        movie_id=movie_id,
        auditorium_id=auditorium_id,
        starts_at=starts_at,
        child_price_cents=child,
        adult_price_cents=adult,
        senior_price_cents=senior,
    )
    db.session.add(s)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return _bad_request("A showtime in this auditorium at this start time already exists.", code=409)

    return jsonify(_to_dict(s)), 201


def get_showtime(showtime_id):
    """
    GET /api/v1/showtimes/<uuid:showtime_id>  (we'll keep <string> and cast in SQLA)
    """
    s = Showtime.query.filter_by(showtime_id=showtime_id).first()
    if not s:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Showtime not found"}}), 404
    return jsonify(_to_dict(s))


def get_showtimes():
    """
    GET /api/v1/showtimes
    Query params:
      movie_id        (int)    filter
      auditorium_id   (int)    filter
      from            (iso dt) lower bound (inclusive) on starts_at
      to              (iso dt) upper bound (exclusive) on starts_at
      limit           (int)    default 20, max 100
      offset          (int)    default 0
      sort            (str)    created_at not present; use starts_at.asc/starts_at.desc (default desc)
    """
    # filters
    movie_id = request.args.get("movie_id", type=int)
    auditorium_id = request.args.get("auditorium_id", type=int)

    from_raw = request.args.get("from")
    to_raw = request.args.get("to")
    dt_from = _parse_dt(from_raw) if from_raw else None
    dt_to = _parse_dt(to_raw) if to_raw else None
    if from_raw and not dt_from:
        return _bad_request("`from` must be ISO datetime")
    if to_raw and not dt_to:
        return _bad_request("`to` must be ISO datetime")

    limit = request.args.get("limit", default=20, type=int)
    offset = request.args.get("offset", default=0, type=int)
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    sort = (request.args.get("sort") or "starts_at.desc").lower()
    order_clause = desc(Showtime.starts_at) if sort == "starts_at.desc" else asc(Showtime.starts_at)

    q = Showtime.query

    if movie_id is not None:
        q = q.filter(Showtime.movie_id == movie_id)
    if auditorium_id is not None:
        q = q.filter(Showtime.auditorium_id == auditorium_id)
    if dt_from:
        q = q.filter(Showtime.starts_at >= dt_from)
    if dt_to:
        q = q.filter(Showtime.starts_at < dt_to)

    total = q.count()
    rows = q.order_by(order_clause).offset(offset).limit(limit).all()

    return jsonify({
        "data": [_to_dict(s) for s in rows],
        "page": {"limit": limit, "offset": offset, "total": total}
    })
