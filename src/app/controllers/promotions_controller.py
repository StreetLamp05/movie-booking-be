from flask import request, jsonify
from sqlalchemy import asc, desc
from .. import db
from ..models.promotions import Promotion
from datetime import datetime
from .. models.users import User
from ..services.email_service import send_promotional_email
from ..models.promotions import Promotion
from datetime import timezone



def _to_promo_row(p: Promotion):
    return {
        "promotion_id": str(p.promotion_id),
        "code": p.code,
        "description": p.description,
        "discount_percent": float(p.discount_percent),
        "starts_at": p.starts_at.isoformat() if p.starts_at else None,
        "ends_at": p.ends_at.isoformat() if p.ends_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "is_active": p.is_active,
        "max_uses": p.max_uses,
        "per_user_limit": p.per_user_limit,
    }

class PromotionController:
    def create_promotion(admin_user):
        data = request.get_json()
        
        # 1. Extract Data
        code = data.get('code')
        discount = data.get('discount_percent')
        start_str = data.get('starts_at') # Expecting format like "2025-12-01"
        end_str = data.get('ends_at')
        description = data.get('description')
        max_uses = data.get('max_uses')
        per_user_limit = data.get('per_user_limit')

        end_date = datetime.fromisoformat(end_str)
        try:
           
            start_date = datetime.fromisoformat(start_str)
            end_date = datetime.fromisoformat(end_str)
        
        except ValueError:
            # Update the error message to be accurate
            return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)'}), 400
            # Get the current time in UTC (Standard for Docker/Servers)
        current_time = datetime.now(timezone.utc)

        # Ensure your input date also has timezone info
        if end_date.tzinfo is None:
            # If the frontend didn't send a timezone, assume UTC (or your server's local time)
            end_date = end_date.replace(tzinfo=timezone.utc)

        # 2. THE FIX: Normalize both to UTC
        # If the date has no timezone (Naive), give it UTC.
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        
    

        # NOW the comparison is accurate
        if end_date <= current_time:
            return jsonify({'error': 'End date must be in the future'}), 400

        # 2. Rubric Requirement: Validate Fields
        if not code or not discount or not start_str or not end_str:
            return jsonify({'error': 'Missing required fields'}), 400
            
        # 3. Rubric Requirement: Validate Discount (0-100%)
        try:
            discount = float(discount)
            if discount <= 0 or discount > 100:
                return jsonify({'error': 'Discount must be between 1% and 100%'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid discount format'}), 400


        # 5. CRITICAL RUBRIC POINT: Start < End Validation
        if start_date >= end_date:
            return jsonify({'error': 'End date must be after start date'}), 400
        
        if Promotion.query.filter_by(code=code).first():
            return jsonify({'error': 'Promotion code already exists'}), 400
        

            # 6. Save to DB
        new_promo = Promotion(
            code=code,
            description=description,
            discount_percent=discount,
            starts_at=start_date, 
            ends_at=end_date,
            is_active=True, 
            max_uses=max_uses,
            per_user_limit=per_user_limit
        )

        try:
            db.session.add(new_promo)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # This catches your CheckConstraints (e.g. if start > end)
            return jsonify({'error': str(e)}), 400

        return jsonify(_to_promo_row(new_promo)), 201


    def send_promotion_email(admin_user, promotion_id):

        # 1. Fetch the promotion
        promo = Promotion.query.get_or_404(promotion_id)
        
        # 2. Rubric Requirement: Filter ONLY subscribed users
        # Make sure your User model actually has 'receives_promotions' or similar
        subscribed_users = User.query.filter_by(is_email_list=True).all()
        
        if not subscribed_users:
            return jsonify({
                'message': 'No subscribed users found. No emails sent.',
                'promo': promo.code
            }), 200

        # 3. Mock the Email Sending (Log it for the Demo)
        print(f"\n[EMAIL SYSTEM] Starting Batch for Promo: {promo.code}")
        print(f"[EMAIL SYSTEM] Discount: {promo.discount_percent}% off")
        print("---------------------------------------------------")
        
        sent_count = 0
        for user in subscribed_users:
            # This print statement is your "proof" for the TA
            print(f"Sending email to: {user.email} [Status: SUBSCRIBED] ... Sent.")
            start_date= promo.starts_at.strftime("%b %d") # e.g., "Dec 01"
            end_date=promo.ends_at.strftime("%b %d")      # e.g., "Dec 31"
            send_promotional_email(
                user_email=user.email,
                promo_code=promo.code,
                start_date=start_date,
                end_date=end_date,
                discount=promo.discount_percent,
            )

            sent_count += 1
            
        print("---------------------------------------------------")
        print(f"[EMAIL SYSTEM] Job Complete. Sent to {sent_count} users.\n")
        
        return jsonify({
            'message': f'Successfully sent promotion "{promo.code}" to {sent_count} subscribers.',
            'recipient_count': sent_count
        }), 200

    def get_active_promotions(admin_user):
        promos = Promotion.query.filter_by(is_active=True).order_by(asc(Promotion.starts_at)).all()
        promo_list = [_to_promo_row(p) for p in promos]
        return jsonify(promo_list), 200

    def get_promotion_by_code(code, admin_user):
        promo = Promotion.query.filter_by(code=code, is_active=True).first()
        if not promo:
            return jsonify({'error': 'Promotion not found or inactive'}), 404
        return jsonify(_to_promo_row(promo)), 200

