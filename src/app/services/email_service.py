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

PASSWORD_CHANGED_EMAIL_TEMPLATE = """
<h2>Password Changed</h2>
<p>Hi {{ email_local }},</p>
<p>Your password was successfully changed.</p>

<h3>Change Details:</h3>
<ul>
  <li><strong>Time:</strong> {{ timestamp }}</li>
  <li><strong>IP Address:</strong> {{ ip_address }}</li>
  <li><strong>Device:</strong> {{ user_agent }}</li>
</ul>

<p><strong>If this wasn't you,</strong> reset your password immediately and contact support.</p>
<p>If it was you, no action is needed.</p>
"""

PROMOTION_EMAIL_TEMPLATE = """
<h1>Exclusive Offer Just For You!</h1>
<p>We have an exclusive promotion for you:</p>

<div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
    <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">USE CODE</p>
    <h2 style="margin: 0; font-size: 36px; letter-spacing: 4px; color: #667eea; font-weight: bold;">{{ promo_code }}</h2>
    <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">{{ discount_percent }}% OFF</p>
</div>

<p><strong>Offer Details:</strong></p>
<ul>
    <li>Discount: {{ discount_percent }}% off</li>
    <li>Valid from: {{ start_date }}</li>
    <li>Valid until: {{ end_date }}</li>
    {% if description %}<li>{{ description }}</li>{% endif %}
</ul>

<p>Don't miss this opportunity! Book your movie tickets today with this exclusive code.</p>
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

def send_password_changed_email(user_email: str, time_str: str, ip: str, ua: str):
    """
    Send password changed notification email with change details
    
    """
    # Extract local part of email (before @) for greeting
    email_local = user_email.split('@')[0] if '@' in user_email else user_email
    
    msg = Message(
        'Password Changed Notification',
        recipients=[user_email],
        html=render_template_string(
            PASSWORD_CHANGED_EMAIL_TEMPLATE,
            email_local=email_local,
            timestamp=time_str,
            ip_address=ip,
            user_agent=ua
        )
    )
    mail.send(msg)

def send_promotion_email(user_email: str, promo_code: str, discount_percent: float, start_date: str, end_date: str, description: str = None):
    """
    Send promotion email to user with promo code
    """
    msg = Message(
        f'Exclusive Promotion: {promo_code}',
        recipients=[user_email],
        html=render_template_string(
            PROMOTION_EMAIL_TEMPLATE,
            promo_code=promo_code,
            discount_percent=discount_percent,
            start_date=start_date,
            end_date=end_date,
            description=description or ""
        )
    )
    mail.send(msg)

def send_promotion_emails_bulk(user_emails: list, promo_code: str, discount_percent: float, start_date: str, end_date: str, description: str = None):
    """
    Send promotion email to multiple users
    """
    for email in user_emails:
        try:
            send_promotion_email(email, promo_code, discount_percent, start_date, end_date, description)
        except Exception as e:
            current_app.logger.error(f"Failed to send promotion email to {email}: {e}")
            continue
