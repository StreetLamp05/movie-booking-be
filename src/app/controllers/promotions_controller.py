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
        "created_at": p.created_at.isoformat() if p.created_at else None,
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
        is_active = data.get('is_active', True)
        end_date = datetime.fromisoformat(end_str)
        created_at = datetime.now(timezone.utc)
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
            is_active=is_active, 
            max_uses=max_uses,
            per_user_limit=per_user_limit,
            created_at=created_at
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

        
        sent_count = 0
        for user in subscribed_users:
            # This print statement is your "proof" for the TA
            start_date= promo.starts_at.strftime("%b %d, %y") # e.g., "Dec 01"
            end_date=promo.ends_at.strftime("%b %d, %y")      # e.g., "Dec 31"
            send_promotional_email(
                user_email=user.email,
                promo_code=promo.code,
                start_date=start_date,
                end_date=end_date,
                discount=promo.discount_percent,
            )

            sent_count += 1
            
        
        return jsonify({
            'message': f'Successfully sent promotion "{promo.code}" to {sent_count} subscribers.',
            'recipient_count': sent_count
        }), 200

    def get_active_promotions(admin_user):
        promos = Promotion.query.filter_by(is_active=True).order_by(asc(Promotion.starts_at)).all()
        promo_list = [_to_promo_row(p) for p in promos]
        return jsonify(promo_list), 200
    
    def get_promotions(admin_user, search_query="", sort_param=""):
        query = Promotion.query

        # 1. Search Filter
        if search_query:
            query = query.filter(
                Promotion.code.ilike(f"%{search_query}%") | 
                Promotion.description.ilike(f"%{search_query}%")
            )

        # 2. Define Sorting Logic
        # Map the string values from React (SortField) to SQLAlchemy columns
        field_mapping = {
            'created_at': Promotion.created_at,
            'code': Promotion.code,
            'discount_percent': Promotion.discount_percent
        }
        
        # Default sorting (Newest first)
        sort_column = Promotion.created_at
        sort_direction = 'desc'

        # 3. Parse the "field.direction" string
        if sort_param and '.' in sort_param:
            try:
                # React sends "code.asc", so we split by the dot
                field_name, direction_str = sort_param.split('.', 1)
                
                # Get the column, defaulting to created_at if the field name is invalid
                sort_column = field_mapping.get(field_name, Promotion.created_at)
                
                # Capture direction
                sort_direction = direction_str
            except ValueError:
                # Fallback if split fails
                pass

        # 4. Apply Sort to Query
        if sort_direction == 'asc':
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # 5. Execute and Return
        promos = query.all()
        promo_list = [_to_promo_row(p) for p in promos]
        return jsonify({"data": promo_list}), 200

    def get_promotion_by_code(code, admin_user):
        promo = Promotion.query.filter_by(code=code, is_active=True).first()
        if not promo:
            return jsonify({'error': 'Promotion not found or inactive'}), 404
        return jsonify(_to_promo_row(promo)), 200
    
    def edit_promotion(admin_user, promotion_id):
        data = request.get_json()
        promo = Promotion.query.get_or_404(promotion_id)

        # Update fields if provided
        for field in ['code', 'description', 'discount_percent', 'starts_at', 'ends_at', 'is_active', 'max_uses', 'per_user_limit']:
            if field in data:
                setattr(promo, field, data[field])

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

        return jsonify(_to_promo_row(promo)), 200
    
    def delete_promotion(admin_user, promotion_id):
        promo = Promotion.query.get_or_404(promotion_id)

        try:
            db.session.delete(promo)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

        return jsonify({'message': 'Promotion deleted successfully'}), 200

