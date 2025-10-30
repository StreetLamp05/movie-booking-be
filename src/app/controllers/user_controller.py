from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from .. import db
from ..models.users import User
from ..models.billing_info import BillingInfo
import re
import uuid
import jwt
import os

def get_user_from_token():
    """Extract user from JWT token in Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None, (jsonify({'error': 'Authorization header is missing'}), 401)
    
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, os.environ.get('JWT_SECRET_KEY', 'your-secret-key'), algorithms=['HS256'])
        user = User.query.filter_by(user_id=payload['user_id']).first()
        
        if not user:
            return None, (jsonify({'error': 'User not found'}), 404)
        if not user.is_verified:
            return None, (jsonify({'error': 'Email is not verified'}), 401)

        
        return user, None
    except jwt.ExpiredSignatureError:
        return None, (jsonify({'error': 'Token has expired'}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({'error': 'Invalid token'}), 401)
    except Exception as e:
        return None, (jsonify({'error': f'Authentication failed: {str(e)}'}), 401)


def _user_to_dict(user: User, include_cards=False):
    data = {
        "user_id": str(user.user_id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_email_list": user.is_email_list,
        "phone_number": user.phone_number,
        "address": {
            "street": user.home_street,
            "city": user.home_city,
            "state": user.home_state,
            "country": user.home_country,
            "zip_code": user.home_zip_code
        }
    }
    
    if include_cards:
        cards = BillingInfo.query.filter_by(user_id=user.user_id).all()
        data["payment_cards"] = [{
            "billing_info_id": str(card.billing_info_id),
            "card_type": card.card_type,
            "card_number": f"****{card.card_number[-4:]}",  # Only show last 4 digits
            "card_exp": card.card_exp,
            "billing_address": {
                "street": card.billing_street,
                "state": card.billing_state,
                "zip_code": card.billing_zip_code
            }
        } for card in cards]
    
    return data

def get_user_profile():
    """GET /api/v1/users/profile"""
    user, error = get_user_from_token()
    if error:
        return error
    
    return jsonify(_user_to_dict(user, include_cards=True))

def update_user_profile():
    """PUT /api/v1/users/profile"""
    user, error = get_user_from_token()
    if error:
        return error
    
    data = request.get_json(silent=True) or {}
    
# Update da info
    if "first_name" in data:
        user.first_name = data["first_name"]
    if "last_name" in data:
        user.last_name = data["last_name"]
    if "phone_number" in data:
        # 10 digit phone number
        phone = re.sub(r'\D', '', data["phone_number"])  # Remove dashes and such
        if len(phone) != 10:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Phone number must be 10 digits"}}), 400
        user.phone_number = phone
    
    # address update
    address = data.get("address", {})
    if address:
        user.home_street = address.get("street", user.home_street)
        user.home_city = address.get("city", user.home_city)
        user.home_state = address.get("state", user.home_state)
        user.home_country = address.get("country", user.home_country)
        user.home_zip_code = address.get("zip_code", user.home_zip_code)
    
    # pref
    if "is_email_list" in data:
        user.is_email_list = bool(data["is_email_list"])
    
    # Update password if provided
    if "password" in data:
        # Once implemented hash password
        user.password_hash = data["password"]
    
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409
    
    return jsonify(_user_to_dict(user, include_cards=True))

def get_user_cards():
    """GET /api/v1/users/cards"""
    user, error = get_user_from_token()
    if error:
        return error
    
    cards = BillingInfo.query.filter_by(user_id=user.user_id).all()
    return jsonify([{
        "billing_info_id": str(card.billing_info_id),
        "card_type": card.card_type,
        "card_number": f"****{card.card_number[-4:]}",
        "card_exp": card.card_exp,
        "billing_address": {
            "street": card.billing_street,
            "state": card.billing_state,
            "zip_code": card.billing_zip_code
        }
    } for card in cards])

def add_user_card():
    """POST /api/v1/users/cards"""
    user, error = get_user_from_token()
    if error:
        return error
    
    # check against limit
    card_count = BillingInfo.query.filter_by(user_id=user.user_id).count()
    if card_count >= 4:
        return jsonify({
            "error": {
                "code": "CONFLICT",
                "message": "Maximum number of cards (4) reached"
            }
        }), 409
    
    data = request.get_json(silent=True) or {}
    required = ["card_type", "card_number", "card_exp", "billing_street", "billing_state", "billing_zip_code"]
    if not all(k in data for k in required):
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": f"Missing required fields: {', '.join(required)}"
            }
        }), 400
    
    # Card num 16 digs
    card_number = re.sub(r'\D', '', data["card_number"])
    if len(card_number) != 16:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "Card number must be 16 digits"
            }
        }), 400
    
    # validate MM/YY
    if not re.match(r'^\d{2}/\d{2}$', data["card_exp"]):
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "Card expiration must be in MM/YY format"
            }
        }), 400
    
    card = BillingInfo(
        user_id=user.user_id,
        card_type=data["card_type"],
        card_number=card_number,
        card_exp=data["card_exp"],
        billing_street=data["billing_street"],
        billing_state=data["billing_state"],
        billing_zip_code=data["billing_zip_code"],
        # Copy name from user profile
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    db.session.add(card)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409
    
    return jsonify({
        "billing_info_id": str(card.billing_info_id),
        "card_type": card.card_type,
        "card_number": f"****{card.card_number[-4:]}",
        "card_exp": card.card_exp,
        "billing_address": {
            "street": card.billing_street,
            "state": card.billing_state,
            "zip_code": card.billing_zip_code
        }
    }), 201

def delete_user_card(card_id):
    """DELETE /api/v1/users/cards/:id"""
    user, error = get_user_from_token()
    if error:
        return error
    
    card = BillingInfo.query.get(card_id)
    if not card or card.user_id != user.user_id:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Card not found"}}), 404
    
    db.session.delete(card)
    db.session.commit()
    return "", 204