from flask import Blueprint, request
from ..middleware.auth import require_admin
from ..controllers.admin_controller import list_users, create_user, update_user_admin, get_user_cards, delete_user_card
from ..controllers.promotions_controller import list_promotions, create_promotion, update_promotion, delete_promotion, send_promotion_emails

bp = Blueprint("admin_routes", __name__, url_prefix="/admin")

# GET /api/v1/admin/users
@bp.get("/users")
@require_admin
def _list_users(admin_user):
    return list_users(admin_user)

# POST /api/v1/admin/users
@bp.post("/users")
@require_admin
def _create_user(admin_user):
    return create_user(admin_user)

# PATCH /api/v1/admin/users/<user_id>
@bp.patch("/users/<user_id>")
@require_admin
def _update_user_admin(admin_user, user_id):
    return update_user_admin(admin_user, user_id)

# GET /api/v1/admin/users/<user_id>/cards
@bp.get("/users/<user_id>/cards")
@require_admin
def _get_user_cards(admin_user, user_id):
    return get_user_cards(admin_user, user_id)

# DELETE /api/v1/admin/users/<user_id>/cards/<card_id>
@bp.delete("/users/<user_id>/cards/<card_id>")
@require_admin
def _delete_user_card(admin_user, user_id, card_id):
    return delete_user_card(admin_user, user_id, card_id)


# GET /api/v1/admin/promotions
@bp.get("/promotions")
@require_admin
def _list_promotions(admin_user):
    return list_promotions(admin_user)

# POST /api/v1/admin/promotions
@bp.post("/promotions")
@require_admin
def _create_promotion(admin_user):
    return create_promotion(admin_user)

# PATCH /api/v1/admin/promotions/<promotion_id>
@bp.patch("/promotions/<promotion_id>")
@require_admin
def _update_promotion(admin_user, promotion_id):
    return update_promotion(admin_user, promotion_id)

# DELETE /api/v1/admin/promotions/<promotion_id>
@bp.delete("/promotions/<promotion_id>")
@require_admin
def _delete_promotion(admin_user, promotion_id):
    return delete_promotion(admin_user, promotion_id)

# POST /api/v1/admin/promotions/<promotion_id>/send-email
@bp.post("/promotions/<promotion_id>/send-email")
@require_admin
def _send_promotion_emails(admin_user, promotion_id):
    return send_promotion_emails(admin_user, promotion_id)
