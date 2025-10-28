"""A collection of utility functions for user authentication"""
from functools import wraps
from flask import jsonify, request
import os
import jwt
from ..models.users import User

def get_user_from_token(token: str) -> User:
    """Get the user from a JWT token"""
    try:
        payload = jwt.decode(token, os.environ.get('JWT_SECRET_KEY', 'your-secret-key'), algorithms=['HS256'])
        return User.query.filter_by(user_id=payload['user_id']).first()
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def require_auth(f):
    """Decorator to require authentication for a route"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header is missing'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            user = get_user_from_token(token)
            if not user:
                return jsonify({'error': 'Invalid or expired token'}), 401
            return f(user, *args, **kwargs)
        except Exception:
            return jsonify({'error': 'Invalid authorization header'}), 401
    return decorated

def require_verified_email(f):
    """Decorator to require verified email for a route"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header is missing'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            user = get_user_from_token(token)
            if not user:
                return jsonify({'error': 'Invalid or expired token'}), 401
            if not user.is_verified:
                return jsonify({'error': 'Email verification required'}), 403
            return f(user, *args, **kwargs)
        except Exception:
            return jsonify({'error': 'Invalid authorization header'}), 401
    return decorated