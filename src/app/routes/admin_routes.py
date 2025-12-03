from flask import Blueprint, request
from ..middleware.auth import require_admin
from ..controllers.admin_controller import list_users, update_user_admin
from ..controllers.promotions_controller import PromotionController

bp = Blueprint("admin_routes", __name__, url_prefix="/admin")

# GET /api/v1/admin/users
@bp.get("/users")
@require_admin
def _list_users(admin_user):
    return list_users(admin_user)

# PATCH /api/v1/admin/users/<user_id>
@bp.patch("/users/<user_id>")
@require_admin
def _update_user_admin(admin_user, user_id):
    return update_user_admin(admin_user, user_id)

# POST /api/v1/admin/promotions
@bp.post("/promotions")
@require_admin
def create_promotion(admin_user):
    return PromotionController.create_promotion(admin_user)

# POST /api/v1/admin/promotions/<promotion_id>/send-email
@bp.post("/promotions/<promotion_id>/send-email")
@require_admin
def send_promotion_email(admin_user, promotion_id):
    return PromotionController.send_promotion_email(admin_user, promotion_id)

# GET /api/v1/admin/promotions?query=...&sort=..
@bp.get("/promotions")
@require_admin
def get_active_promotions(admin_user):
    search_query = request.args.get("query", "")
    sort_order = request.args.get("sort", "")
    return PromotionController.get_promotions(admin_user, search_query, sort_order)

# GET /api/v1/admin/promotions/<code>
@bp.get("/promotions/<code>")
def get_promotion_by_code(code, admin_user):
    return PromotionController.get_promotion_by_code(code, admin_user)

# PATCH api/v1/admin/promotions/${promotionId}
@bp.patch("/promotions/<promotion_id>")
@require_admin
def update_promotion(admin_user, promotion_id):
    return PromotionController.edit_promotion(admin_user, promotion_id)

# DELETE api/v1/admin/promotions/${promotionId}
@bp.delete("/promotions/<promotion_id>")
@require_admin
def delete_promotion(admin_user, promotion_id):
    return PromotionController.delete_promotion(admin_user, promotion_id)
