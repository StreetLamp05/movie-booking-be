from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from .. import db
from ..models.users import User
from ..models.billing_info import BillingInfo
import re
import uuid

# Hardcoded for now
TEST_USER_ID = "123e4567-e89b-12d3-a456-426614174000"


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
    # create the test if not exist
    user = User.query.filter_by(user_id=uuid.UUID(TEST_USER_ID)).first()
    if not user:
        user = User(
            user_id=uuid.UUID(TEST_USER_ID),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="test123",
            is_email_list=True
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": {"code": "CONFLICT", "message": "Failed to create test user"}}), 409
    
    return jsonify(_user_to_dict(user, include_cards=True))

def update_user_profile():
    """PUT /api/v1/users/profile"""
    user = User.query.filter_by(user_id=uuid.UUID(TEST_USER_ID)).first()
    if not user:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404
    
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
    cards = BillingInfo.query.filter_by(user_id=uuid.UUID(TEST_USER_ID)).all()
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
    # check against limit
    card_count = BillingInfo.query.filter_by(user_id=uuid.UUID(TEST_USER_ID)).count()
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
    
    user = User.query.filter_by(user_id=uuid.UUID(TEST_USER_ID)).first()
    card = BillingInfo(
        user_id=uuid.UUID(TEST_USER_ID),
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
    card = BillingInfo.query.get(card_id)
    if not card or str(card.user_id) != TEST_USER_ID:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Card not found"}}), 404
    
    db.session.delete(card)
    db.session.commit()
    return "", 204