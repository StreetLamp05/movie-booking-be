from flask import jsonify, request, current_app, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone

from ..models.users import User
from ..models.verification_tokens import VerificationToken
from ..models.password_reset_tokens import PasswordResetToken
from ..services.email_service import (
    send_verification_email,
    generate_verification_code,
    send_password_reset_email,
    send_password_changed_email,
)
from .. import db

try:
    import jwt
except ImportError:
    jwt = None


def _now_utc():
    return datetime.now(timezone.utc)


def _get_jwt_from_request():
    """Prefer cookie; fallback to Authorization: Bearer"""
    token = request.cookies.get(current_app.config["JWT_COOKIE_NAME"])
    if token:
        return token
    auth = request.headers.get("Authorization") or ""
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    return None


class AuthController:
    @staticmethod
    def signup():
        data = request.get_json(silent=True) or {}

        required_fields = ["first_name", "last_name", "email", "password"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return (
                jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}),
                400,
            )

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already registered"}), 409

        user = User(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            password_hash=generate_password_hash(data["password"]),
            is_email_list=bool(data.get("is_email_list", False)),
        )

        try:
            db.session.add(user)
            db.session.flush()  # get user_id

            code = generate_verification_code()
            vtok = VerificationToken(user_id=user.user_id, token=code)
            db.session.add(vtok)
            db.session.commit()

            try:
                send_verification_email(user.email, code)
            except Exception as e:
                current_app.logger.error(f"Failed to send verification email: {e}")

            return (
                jsonify(
                    {
                        "message": "User created. Check your email for a verification code."
                    }
                ),
                201,
            )
        except Exception as e:
            db.session.rollback
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def login():
        if jwt is None:
            return jsonify({"error": "JWT module not available"}), 500

        data = request.get_json(silent=True) or {}
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid email or password"}), 401

        # Require email verification before login
        if not user.is_verified:
            return (
                jsonify(
                    {
                        "error": "Email not verified. Please verify your email before logging in."
                    }
                ),
                403,
            )

        exp = _now_utc() + timedelta(days=current_app.config["JWT_EXPIRES_DAYS"])
        try:
            token = jwt.encode(
                {"user_id": str(user.user_id), "exp": exp},
                current_app.config["JWT_SECRET_KEY"],
                algorithm="HS256",
            )
        except Exception as e:
            return jsonify({"error": f"Failed to generate token: {str(e)}"}), 500

        payload = {
            "user": {
                "user_id": str(user.user_id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": bool(user.is_admin),  # legacy flag
                "role": "admin" if user.is_admin else "user",
                "is_verified": bool(user.is_verified),
            }
        }

        resp = make_response(jsonify(payload), 200)
        resp.set_cookie(
            current_app.config["JWT_COOKIE_NAME"],
            token,
            httponly=True,
            secure=current_app.config["JWT_COOKIE_SECURE"],
            samesite=current_app.config["JWT_COOKIE_SAMESITE"],
            path="/",
            max_age=int(
                timedelta(days=current_app.config["JWT_EXPIRES_DAYS"]).total_seconds()
            ),
        )
        return resp

    @staticmethod
    def logout():
        resp = make_response(jsonify({"message": "Logged out"}), 200)
        resp.set_cookie(
            current_app.config["JWT_COOKIE_NAME"],
            "",
            httponly=True,
            secure=current_app.config["JWT_COOKIE_SECURE"],
            samesite=current_app.config["JWT_COOKIE_SAMESITE"],
            path="/",
            max_age=0,
        )
        return resp

    @staticmethod
    def verify_email():
        data = request.get_json(silent=True) or {}
        email = data.get("email")
        code = data.get("code")
        if not email or not code:
            return (
                jsonify({"error": "Email and verification code are required"}),
                400,
            )

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        vtok = VerificationToken.query.filter_by(
            user_id=user.user_id, token=code
        ).first()
        if not vtok:
            return jsonify({"error": "Invalid verification code"}), 400
        if vtok.is_expired:
            db.session.delete(vtok)
            db.session.commit()
            return jsonify({"error": "Verification code has expired"}), 400
        if vtok.is_used:
            return jsonify({"error": "Verification code has already been used"}), 400

        user.is_verified = True
        vtok.is_used = True
        db.session.commit()
        return jsonify({"message": "Email verified successfully"}), 200

    @staticmethod
    def resend_verification():
        if jwt is None:
            return jsonify({"error": "JWT module not available"}), 500

        token = _get_jwt_from_request()
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        try:
            payload = jwt.decode(
                token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        user = User.query.filter_by(user_id=payload["user_id"]).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        if user.is_verified:
            return jsonify({"message": "Email already verified"}), 200

        VerificationToken.query.filter_by(user_id=user.user_id).delete()
        code = generate_verification_code()
        vtok = VerificationToken(user_id=user.user_id, token=code)
        db.session.add(vtok)
        db.session.commit()

        try:
            send_verification_email(user.email, code)
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {e}")
            return jsonify({"error": "Failed to send verification email"}), 500

        return jsonify({"message": "Verification email sent"}), 200

    @staticmethod
    def verify_token():
        if jwt is None:
            return jsonify({"error": "JWT module not available"}), 500

        token = _get_jwt_from_request()
        if not token:
            return jsonify({"error": "Not authenticated"}), 401

        try:
            payload = jwt.decode(
                token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        user = User.query.filter_by(user_id=payload["user_id"]).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        return (
            jsonify(
                {
                    "user_id": str(user.user_id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_verified": bool(user.is_verified),
                    "is_admin": bool(user.is_admin),  # legacy
                    "role": "admin" if user.is_admin else "user",
                }
            ),
            200,
        )

    @staticmethod
    def forgot_password():
        data = request.get_json(silent=True) or {}
        email = data.get("email")
        # Always 200 for privacy
        if not email:
            return (
                jsonify(
                    {"message": "If that email exists, a reset code will be sent."}
                ),
                200,
            )

        user = User.query.filter_by(email=email).first()
        if user:
            try:
                PasswordResetToken.query.filter_by(
                    user_id=user.user_id, is_used=False
                ).delete()
                code = PasswordResetToken.generate_code()
                rtok = PasswordResetToken(user_id=user.user_id, token=code)
                db.session.add(rtok)
                db.session.commit()
                try:
                    send_password_reset_email(user.email, code)
                except Exception as e:
                    current_app.logger.error(
                        f"Failed to send password reset email: {e}"
                    )
            except Exception as e:
                current_app.logger.error(
                    f"Failed to create password reset token: {e}"
                )

        return (
            jsonify(
                {"message": "If that email exists, a reset code will be sent."}
            ),
            200,
        )

    @staticmethod
    def reset_password():
        data = request.get_json(silent=True) or {}
        email = data.get("email")
        code = data.get("code")
        new_password = data.get("new_password")
        if not email or not code or not new_password:
            return (
                jsonify({"error": "Email, code and new_password are required"}),
                400,
            )

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "Invalid email or code"}), 400

        rtok = PasswordResetToken.query.filter_by(
            user_id=user.user_id, token=code
        ).first()
        if not rtok:
            return jsonify({"error": "Invalid email or code"}), 400
        if rtok.is_used:
            return jsonify({"error": "Code has already been used"}), 400
        if rtok.is_expired:
            db.session.delete(rtok)
            db.session.commit()
            return jsonify({"error": "Code has expired"}), 400

        try:
            user.password_hash = generate_password_hash(new_password)
            rtok.is_used = True
            PasswordResetToken.query.filter(
                PasswordResetToken.user_id == user.user_id,
                PasswordResetToken.is_used == False,
                PasswordResetToken.token != code,
            ).delete()
            db.session.commit()
            
            # Notify user about password change
            try:
                from datetime import datetime, timezone
                time_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                ip = request.remote_addr or "unknown"
                ua = request.headers.get("User-Agent")
                send_password_changed_email(user.email, time_str, ip, ua)
            except Exception as e:
                current_app.logger.error(f"Failed to send password-changed email: {e}")
            
            return jsonify({"message": "Password updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update password: {str(e)}"}), 500
