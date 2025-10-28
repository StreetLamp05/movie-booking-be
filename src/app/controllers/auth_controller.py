from flask import jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from ..models.users import User
from ..models.verification_tokens import VerificationToken
from ..services.email_service import send_verification_email, generate_verification_code, send_password_reset_email
from ..models.password_reset_tokens import PasswordResetToken
from .. import db
from datetime import datetime, timedelta, timezone
import os

try:
    import jwt
except ImportError as e:
    print(f"Error importing JWT: {str(e)}")
    jwt = None

class AuthController:
    @staticmethod
    def signup():
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409

        # Create new user
        user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            is_email_list=bool(data.get('is_email_list', False))
        )

        try:
            # Create and save the user
            db.session.add(user)
            db.session.flush()  # Get the user ID without committing
            
            # Generate verification code
            code = generate_verification_code()
            verification_token = VerificationToken(
                user_id=user.user_id,
                token=code
            )
            db.session.add(verification_token)
            db.session.commit()
            
            # Send verification email
            try:
                send_verification_email(user.email, code)
            except Exception as e:
                current_app.logger.error(f"Failed to send verification email: {str(e)}")
                # Continue anyway - we can always resend the verification email
            
            return jsonify({'message': 'User created successfully. Please check your email to verify your account.'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @staticmethod
    def login():
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400

        # Find user
        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401

        # Generate JWT token
        if jwt is None:
            return jsonify({'error': 'JWT module not available'}), 500
            
        try:
            token = jwt.encode({
                'user_id': str(user.user_id),
                'exp': datetime.now(timezone.utc) + timedelta(days=1)
            }, os.environ.get('JWT_SECRET_KEY', 'your-secret-key'))
        except Exception as e:
            return jsonify({'error': f'Failed to generate token: {str(e)}'}), 500

        return jsonify({
            'token': token,
            'user': {
                'user_id': str(user.user_id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_admin': bool(user.is_admin)
            }
        }), 200

    @staticmethod
    def verify_email():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
            
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({'error': 'Email and verification code are required'}), 400

        # Find user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Find verification token
        verification_token = VerificationToken.query.filter_by(
            user_id=user.user_id,
            token=code
        ).first()
        
        if not verification_token:
            return jsonify({'error': 'Invalid verification code'}), 400

        if verification_token.is_expired:
            db.session.delete(verification_token)
            db.session.commit()
            return jsonify({'error': 'Verification code has expired'}), 400

        if verification_token.is_used:
            return jsonify({'error': 'Verification code has already been used'}), 400

        # Mark user as verified and token as used
        user.is_verified = True
        verification_token.is_used = True
        db.session.commit()

        return jsonify({'message': 'Email verified successfully'}), 200

    @staticmethod
    def forgot_password():
        data = request.get_json(silent=True) or {}
        email = data.get('email')
        if not email:
            return jsonify({'message': 'If that email exists, a reset code will be sent.'}), 200

        user = User.query.filter_by(email=email).first()
        if user:
            try:
                # delete prior unused tokens for cleanliness
                from .. import db
                PasswordResetToken.query.filter_by(user_id=user.user_id, is_used=False).delete()
                code = PasswordResetToken.generate_code()
                reset_token = PasswordResetToken(user_id=user.user_id, token=code)
                db.session.add(reset_token)
                db.session.commit()

                try:
                    send_password_reset_email(user.email, code)
                except Exception as e:
                    current_app.logger.error(f"Failed to send password reset email: {str(e)}")
            except Exception as e:
                current_app.logger.error(f"Failed to create password reset token: {str(e)}")
        # Always respond with 200 to prevent user enumeration
        return jsonify({'message': 'If that email exists, a reset code will be sent.'}), 200

    @staticmethod
    def reset_password():
        data = request.get_json(silent=True) or {}
        email = data.get('email')
        code = data.get('code')
        new_password = data.get('new_password')
        if not email or not code or not new_password:
            return jsonify({'error': 'Email, code and new_password are required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Invalid email or code'}), 400

        reset_token = PasswordResetToken.query.filter_by(user_id=user.user_id, token=code).first()
        if not reset_token:
            return jsonify({'error': 'Invalid email or code'}), 400
        if reset_token.is_used:
            return jsonify({'error': 'Code has already been used'}), 400
        if reset_token.is_expired:
            from .. import db
            db.session.delete(reset_token)
            db.session.commit()
            return jsonify({'error': 'Code has expired'}), 400

        # Set new password
        try:
            from .. import db
            user.password_hash = generate_password_hash(new_password)
            reset_token.is_used = True
            # Optionally delete other tokens
            PasswordResetToken.query.filter(
                PasswordResetToken.user_id == user.user_id,
                PasswordResetToken.is_used == False,
                PasswordResetToken.token != code
            ).delete()
            db.session.commit()
            return jsonify({'message': 'Password updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to update password: {str(e)}'}), 500

    @staticmethod
    def resend_verification():
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header is missing'}), 401

        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, os.environ.get('JWT_SECRET_KEY', 'your-secret-key'), algorithms=['HS256'])
            user = User.query.filter_by(user_id=payload['user_id']).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404

            if user.is_verified:
                return jsonify({'message': 'Email already verified'}), 200

            # Delete any existing verification tokens
            VerificationToken.query.filter_by(user_id=user.user_id).delete()

            # Generate new verification code
            code = generate_verification_code()
            verification_token = VerificationToken(
                user_id=user.user_id,
                token=code
            )
            db.session.add(verification_token)
            db.session.commit()

            # Send verification email
            try:
                send_verification_email(user.email, code)
            except Exception as e:
                current_app.logger.error(f"Failed to send verification email: {str(e)}")
                return jsonify({'error': 'Failed to send verification email'}), 500

            return jsonify({'message': 'Verification email sent successfully'}), 200

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

    @staticmethod
    def verify_token():
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header is missing'}), 401

        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(token, os.environ.get('JWT_SECRET_KEY', 'your-secret-key'), algorithms=['HS256'])
            user = User.query.filter_by(user_id=payload['user_id']).first()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404

            return jsonify({
                'user_id': str(user.user_id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_verified': user.is_verified,
                'is_admin': bool(user.is_admin)
            }), 200

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401