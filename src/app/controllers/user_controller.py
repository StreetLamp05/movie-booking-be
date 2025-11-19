from flask import request, jsonify, current_app
from datetime import datetime
from ..services.email_service import send_password_changed_email
from ..services.encryption import CardEncryption
from sqlalchemy.exc import IntegrityError
import re
import jwt
from datetime import datetime, timezone
from .. import db
from ..models.users import User
from ..models.billing_info import BillingInfo
from ..services.email_service import send_password_changed_email

STATE_RE = re.compile(r"^[A-Z]{2}$")
ZIP5_RE  = re.compile(r"^\d{5}$")
MMYY_RE  = re.compile(r"^(0[1-9]|1[0-2])/\d{2}$")
CARD16_RE = re.compile(r"^\d{16}$")

def get_user_from_token():
    tok = request.cookies.get(current_app.config["JWT_COOKIE_NAME"])
    if not tok:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            tok = auth.split(" ", 1)[1]
    if not tok:
        return None, (jsonify({"error": "Not authenticated"}), 401)
    try:
        payload = jwt.decode(tok, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        user = User.query.filter_by(user_id=payload["user_id"]).first()
        if not user:
            return None, (jsonify({"error": "User not found"}), 404)
        if not user.is_verified:
            return None, (jsonify({"error": "Email is not verified"}), 401)
        return user, None
    except jwt.ExpiredSignatureError:
        return None, (jsonify({"error": "Token has expired"}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({"error": "Invalid token"}), 401)
    except Exception as e:
        return None, (jsonify({"error": f"Authentication failed: {str(e)}"}), 401)

def _user_to_dict(user: User, include_cards: bool = False):
    data = {
        "user_id": str(user.user_id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_email_list": user.is_email_list,
        "phone_number": user.phone_number,
        "role": "admin" if user.is_admin else "user",
        "is_verified": bool(user.is_verified),
        "address": {
            "street": user.home_street,
            "city": user.home_city,
            "state": user.home_state,
            "country": user.home_country,
            "zip_code": user.home_zip_code,
        },
    }
    if include_cards:
        cards = BillingInfo.query.filter_by(user_id=user.user_id).order_by(BillingInfo.created_at.desc()).all()
        data["payment_cards"] = [_card_to_public_dict(c) for c in cards]
    return data

def _card_to_public_dict(card: BillingInfo):
    """
    Convert BillingInfo to public dict, decrypting sensitive fields.
    Security: Only last 4 digits of card number exposed; full number and expiry are encrypted in DB.
    """
    try:
        encryptor = CardEncryption()
        # Decrypt card number and expiry if they are encrypted
        card_number = encryptor.decrypt(card.card_number) if card.card_number else ""
        card_last4 = card_number[-4:] if card_number else "0000"
        # Decrypt cardholder name and expiry
        cardholder_name = encryptor.decrypt(card.cardholder_name) if card.cardholder_name else ""
        card_exp = encryptor.decrypt(card.card_exp) if card.card_exp else ""
    except Exception as e:
        current_app.logger.warning(f"Failed to decrypt card data: {e}")
        card_last4 = "XXXX"
        cardholder_name = "••••••••"
        card_exp = "••/••"
    
    return {
        "billing_info_id": str(card.billing_info_id),
        "card_type": card.card_type,
        "cardholder_name": cardholder_name,  # Decrypted
        "card_last4": card_last4,
        "card_exp": card_exp,  # Decrypted
        "billing_address": {
            "street": card.billing_street,
            "city": card.billing_city,
            "state": card.billing_state,
            "zip_code": card.billing_zip_code,
        },
        "created_at": card.created_at.isoformat() if card.created_at else None,
    }

# get/ put

def get_user_profile():
    user, error = get_user_from_token()
    if error:
        return error
    return jsonify(_user_to_dict(user, include_cards=True)), 200

def update_user_profile():
    """
    Regular users can edit: first/last name, phone_number (10 digits), address, is_email_list, password
    Email change is admin-only (kept as-is).
    """
    user, error = get_user_from_token()
    if error:
        return error

    data = request.get_json(silent=True) or {}

    # Names
    if "first_name" in data:
        user.first_name = (data["first_name"] or "").strip()
    if "last_name" in data:
        user.last_name = (data["last_name"] or "").strip()

    # Phone
    if "phone_number" in data:
        digits = re.sub(r"\D", "", str(data["phone_number"]))
        if len(digits) != 10:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Phone number must be 10 digits"}}), 400
        user.phone_number = digits

    # Address
    if "address" in data and isinstance(data["address"], dict):
        addr = data["address"]
        if "state" in addr and addr["state"]:
            st = str(addr["state"]).upper()
            if not STATE_RE.match(st):
                return jsonify({"error": {"code": "BAD_REQUEST", "message": "State must be 2-letter US code"}}), 400
            user.home_state = st
        if "zip_code" in addr and addr["zip_code"]:
            z = str(addr["zip_code"])
            if not ZIP5_RE.match(z):
                return jsonify({"error": {"code": "BAD_REQUEST", "message": "ZIP must be 5 digits"}}), 400
            user.home_zip_code = z
        if "street" in addr:
            user.home_street = addr["street"]
        if "city" in addr:
            user.home_city = addr["city"]
        if "country" in addr:
            user.home_country = addr["country"]

    # email list
    if "is_email_list" in data:
        user.is_email_list = bool(data["is_email_list"])

    # Password (inline)
    if "password" in data and data["password"]:
        from werkzeug.security import generate_password_hash
        user.password_hash = generate_password_hash(data["password"])
        # notify user about password change (do not include the password)
        try:
            time_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            ip = request.remote_addr or "unknown"
            ua = request.headers.get("User-Agent")
            send_password_changed_email(user.email, time_str, ip, ua)
        except Exception as e:
            current_app.logger.error(f"Failed to send password-changed email: {e}")

    # Email change (admin-only, unchanged from your rules)
    if "email" in data and data["email"] is not None:
        if not user.is_admin:
            return jsonify({"error": {"code": "FORBIDDEN", "message": "Email cannot be changed"}}), 403
        new_email = (data["email"] or "").strip().lower()
        if not new_email:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Email cannot be empty"}}), 400
        exists = User.query.filter(User.email == new_email, User.user_id != user.user_id).first()
        if exists:
            return jsonify({"error": {"code": "CONFLICT", "message": "Email already in use"}}), 409
        user.email = new_email

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409

    return jsonify(_user_to_dict(user, include_cards=True)), 200

# ===== Billing (GET/POST/PATCH/DELETE) =====

def get_user_cards():
    user, error = get_user_from_token()
    if error:
        return error
    cards = BillingInfo.query.filter_by(user_id=user.user_id).order_by(BillingInfo.created_at.desc()).all()
    return jsonify([_card_to_public_dict(c) for c in cards]), 200

def add_user_card():
    """
    Create a new billing card for user.
    Security: Card number, expiry, and cardholder name are encrypted before storage.
    """
    user, error = get_user_from_token()
    if error:
        return error

    if BillingInfo.query.filter_by(user_id=user.user_id).count() >= 4:
        return jsonify({"error": {"code": "CONFLICT", "message": "Maximum number of cards (4) reached"}}), 409

    data = request.get_json(silent=True) or {}
    required = [
        "card_type",
        "card_number",
        "card_exp",
        "cardholder_name",
        "billing_street",
        "billing_city",
        "billing_state",
        "billing_zip_code",
    ]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": f"Missing: {', '.join(missing)}"}}), 400

    card_type = str(data["card_type"])
    if card_type not in ("debit", "credit"):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "card_type must be 'debit' or 'credit'"}}), 400

    # Validate card number format (16 digits)
    num = re.sub(r"\D", "", str(data["card_number"]))
    if not CARD16_RE.match(num):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "card_number must be 16 digits"}}), 400

    # Validate expiry format (MM/YY)
    exp = str(data["card_exp"])
    if not MMYY_RE.match(exp):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "card_exp must be MM/YY"}}), 400

    # Validate state (2-letter US code)
    state = str(data["billing_state"]).upper()
    if not STATE_RE.match(state):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "billing_state must be 2-letter US code"}}), 400

    # Validate ZIP code (5 digits)
    zip5 = str(data["billing_zip_code"])
    if not ZIP5_RE.match(zip5):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "billing_zip_code must be 5 digits"}}), 400

    # Encrypt sensitive fields
    try:
        encryptor = CardEncryption()
        encrypted_card_number = encryptor.encrypt(num)
        encrypted_card_exp = encryptor.encrypt(exp)
        encrypted_cardholder_name = encryptor.encrypt(str(data["cardholder_name"]))
    except Exception as e:
        current_app.logger.error(f"Encryption failed: {e}")
        return jsonify({"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Failed to process card"}}), 500

    card = BillingInfo(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        cardholder_name=encrypted_cardholder_name,  # Encrypted
        billing_city=str(data["billing_city"]),
        card_type=card_type,
        card_number=encrypted_card_number,  # Encrypted
        card_exp=encrypted_card_exp,  # Encrypted
        billing_street=str(data["billing_street"]),
        billing_state=state,
        billing_zip_code=zip5,
    )

    db.session.add(card)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409

    return jsonify(_card_to_public_dict(card)), 201

def update_user_card(card_id):
    """
    Update card details (expiry, cardholder name, address).
    Security: Card number cannot be updated via PATCH. Sensitive fields are encrypted.
    """
    user, error = get_user_from_token()
    if error:
        return error

    card = BillingInfo.query.get(card_id)
    if not card or card.user_id != user.user_id:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Card not found"}}), 404

    data = request.get_json(silent=True) or {}

    # Encrypt cardholder name if updating
    if "cardholder_name" in data and data["cardholder_name"]:
        try:
            encryptor = CardEncryption()
            card.cardholder_name = encryptor.encrypt(str(data["cardholder_name"]))
        except Exception as e:
            current_app.logger.error(f"Encryption failed: {e}")
            return jsonify({"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Failed to update card"}}), 500

    # Encrypt expiry if updating
    if "card_exp" in data and data["card_exp"]:
        exp = str(data["card_exp"])
        if not MMYY_RE.match(exp):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "card_exp must be MM/YY"}}), 400
        try:
            encryptor = CardEncryption()
            card.card_exp = encryptor.encrypt(exp)
        except Exception as e:
            current_app.logger.error(f"Encryption failed: {e}")
            return jsonify({"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Failed to update card"}}), 500

    # address fields
    addr_map = {
        "billing_street": ("billing_street", None),
        "billing_city":   ("billing_city",   None),
        "billing_state":  ("billing_state",  "state"),
        "billing_zip_code": ("billing_zip_code", "zip"),
    }
    for k, (attr, kind) in addr_map.items():
        if k in data and data[k] is not None:
            val = str(data[k])
            if kind == "state":
                val = val.upper()
                if not STATE_RE.match(val):
                    return jsonify({"error": {"code": "BAD_REQUEST", "message": "billing_state must be 2-letter US code"}}), 400
            if kind == "zip":
                if not ZIP5_RE.match(val):
                    return jsonify({"error": {"code": "BAD_REQUEST", "message": "billing_zip_code must be 5 digits"}}), 400
            setattr(card, attr, val)

    # optional card_type change
    if "card_type" in data and data["card_type"]:
        ct = str(data["card_type"])
        if ct not in ("debit", "credit"):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "card_type must be 'debit' or 'credit'"}}), 400
        card.card_type = ct

    # never allow updating full number via PATCH to avoid mistakes
    if "card_number" in data:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "card_number cannot be updated; create a new card"}}), 403

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409

    return jsonify(_card_to_public_dict(card)), 200

def delete_user_card(card_id):
    user, error = get_user_from_token()
    if error:
        return error

    card = BillingInfo.query.get(card_id)
    if not card or card.user_id != user.user_id:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Card not found"}}), 404

    db.session.delete(card)
    db.session.commit()
    return "", 204
