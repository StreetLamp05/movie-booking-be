from flask import Blueprint
from ..models import User
from .. import db

bp = Blueprint("routes", __name__)

@bp.get("/health")
def health():
    return {"ok": True}

@bp.post("/seed")
def seed():
    u = User(email="test@example.com")
    db.session.add(u)
    db.session.commit()
    return {"created": u.id}, 201
