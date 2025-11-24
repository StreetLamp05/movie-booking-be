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

PROMO_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }
  .container { width: 100%; padding: 20px 0; }
  .card { background-color: #ffffff; max-width: 600px; margin: 0 auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden; }
  .header { background-color: #b91c1c; padding: 20px; text-align: center; }
  .header h1 { color: #ffffff; margin: 0; font-size: 24px; text-transform: uppercase; letter-spacing: 1px; }
  .content { padding: 30px 20px; text-align: center; color: #333333; }
  .discount-text { font-size: 48px; font-weight: bold; color: #b91c1c; margin: 10px 0; }
  .sub-text { font-size: 16px; color: #666666; margin-bottom: 20px; }
  .coupon-box { background-color: #f8f8f8; border: 2px dashed #b91c1c; padding: 15px; display: inline-block; margin: 20px 0; }
  .code { font-size: 28px; font-weight: bold; letter-spacing: 2px; color: #333; }
  .footer { background-color: #eeeeee; padding: 15px; text-align: center; font-size: 12px; color: #888888; }
</style>
</head>
<body>

<div class="container">
  <div class="card">
    <div class="header">
      <h1>Movie Night Special!</h1>
    </div>
    
    <div class="content">
      <p class="sub-text">We noticed you love movies as much as we do. Here is an exclusive treat for your next booking.</p>
      
      <div class="discount-text">{{ discount }}% OFF</div>
      <p>Use this code at checkout:</p>
      
      <div class="coupon-box">
        <span class="code">{{ promo_code }}</span>
      </div>
      
      <p style="font-size: 14px; color: #555;">
        Valid from <strong>{{ start_date }}</strong> to <strong>{{ end_date }}</strong>
      </p>
    </div>

    <div class="footer">
      <p>Hurry! This offer is valid for a limited time only.</p>
      <p>&copy; 2025 Cinema E-Booking System</p>
    </div>
  </div>
</div>

</body>
</html>
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


def send_promotional_email(user_email: str, discount: float, 
                           promo_code: str, start_date: str, end_date: str):
    """
    Send promotional email to the user
    """

    
    msg = Message(
        'New Promotion Just for You!',
        recipients=[user_email],
        html=render_template_string(
            PROMO_TEMPLATE,
            discount=int(discount), # e.g., 20
            promo_code=promo_code,                # e.g., "SUMMER25"
            start_date=start_date,
            end_date=end_date
        )
    )
    mail.send(msg)