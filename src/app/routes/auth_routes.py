from flask import Blueprint
from ..controllers.auth_controller import AuthController

auth_bp = Blueprint("auth", __name__)

# /api/v1/auth/*
@auth_bp.route("/signup", methods=["POST"])
def signup():
    return AuthController.signup()

@auth_bp.route("/login", methods=["POST"])
def login():
    return AuthController.login()

@auth_bp.route("/logout", methods=["POST"])
def logout():
    return AuthController.logout()

# Allow both GET (browser checks) and POST (programmatic)
@auth_bp.route("/verify", methods=["GET", "POST"])
def verify_token():
    return AuthController.verify_token()

@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    return AuthController.verify_email()

@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    return AuthController.resend_verification()

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    return AuthController.forgot_password()

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    return AuthController.reset_password()
