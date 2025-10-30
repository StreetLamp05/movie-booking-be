from flask import Blueprint
from ..middleware.auth import require_admin
from ..controllers.admin_controller import list_users, update_user_admin

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
