"""Auth utilities: extract JWT from HttpOnly cookie (preferred) or Bearer header."""
from functools import wraps
from flask import jsonify, request, current_app
import jwt
from ..models.users import User

def _extract_token():
    # Cookie first
    tok = request.cookies.get(current_app.config["JWT_COOKIE_NAME"])
    if tok:
        return tok
    # Authorization fallback
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None

def _decode_user(token: str):
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        return User.query.filter_by(user_id=payload["user_id"]).first()
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def require_auth(f):
    """Require valid JWT (cookie/Bearer)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        user = _decode_user(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(user, *args, **kwargs)
    return decorated

def require_verified_email(f):
    """Require valid JWT + verified email."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        user = _decode_user(token)
        if not user:
            return jsonify({"error": "Invalid or expired token"}), 401
        if not user.is_verified:
            return jsonify({"error": "Email verification required"}), 403
        return f(user, *args, **kwargs)
    return decorated
