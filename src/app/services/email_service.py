from flask_mail import Mail, Message
from flask import current_app, render_template_string

mail = Mail()

VERIFICATION_EMAIL_TEMPLATE = """
<h1>Welcome to Movie Booking!</h1>
<p>Thank you for creating an account. Please use the verification code below to verify your email address:</p>
<h2 style="text-align: center; font-size: 32px; letter-spacing: 8px; color: #4F46E5;">{{ verification_code }}</h2>
<p>This code will expire in 15 minutes.</p>
<p>If you did not create an account, please ignore this email.</p>
"""

PASSWORD_RESET_EMAIL_TEMPLATE = """
<h1>Reset your password</h1>
<p>We received a request to reset your password. Use the code below to proceed:</p>
<h2 style="text-align: center; font-size: 32px; letter-spacing: 8px; color: #4F46E5;">{{ reset_code }}</h2>
<p>This code will expire in 15 minutes.</p>
<p>If you did not request a password reset, you can ignore this email.</p>
"""

def send_verification_email(user_email: str, code: str):
    """
    Send verification email to the user with a 6-digit code
    """
    msg = Message(
        'Verify your email address',
        recipients=[user_email],
        html=render_template_string(
            VERIFICATION_EMAIL_TEMPLATE,
            verification_code=code
        )
    )
    
    mail.send(msg)

def generate_verification_code() -> str:
    """
    Generate a 6-digit verification code
    """
    from ..models.verification_tokens import VerificationToken
    return VerificationToken.generate_code()

def send_password_reset_email(user_email: str, code: str):
    """
    Send password reset email with a 6-digit code
    """
    msg = Message(
        'Reset your password',
        recipients=[user_email],
        html=render_template_string(
            PASSWORD_RESET_EMAIL_TEMPLATE,
            reset_code=code
        )
    )
    mail.send(msg)