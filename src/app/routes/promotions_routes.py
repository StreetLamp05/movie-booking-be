from flask import Blueprint
from ..middleware.auth import require_admin
from ..controllers.promotions_controller import PromotionController

bp = Blueprint("promotions_routes", __name__, url_prefix="/promo")

# POST /api/v1/promo
@bp.post("")
@require_admin
def create_promotion(admin_user):
    return PromotionController.create_promotion(admin_user)

# POST /api/v1/promo/email/<promotion_id>
@bp.post("/email/<promotion_id>")
@require_admin
def send_promotion_email(admin_user, promotion_id):
    return PromotionController.send_promotion_email(admin_user, promotion_id)

# GET /api/v1/promo
@bp.get("")
@require_admin
def get_active_promotions(admin_user):
    return PromotionController.get_active_promotions(admin_user)

# GET /api/v1/promo/<code>
@bp.get("/<code>")
def get_promotion_by_code(code, admin_user):
    return PromotionController.get_promotion_by_code(code, admin_user)




