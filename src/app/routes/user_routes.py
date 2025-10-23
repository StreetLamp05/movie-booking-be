from flask import Blueprint
from ..controllers.user_controller import (
    create_user,
    get_user,
    get_users,
    edit_user,
    delete_user,
)

bp = Blueprint("user_routes", __name__, url_prefix="/users")

# POST /api/v1/users
bp.post("")(create_user)

# GET /api/v1/users/{user_id}
bp.get("/<user_id>")(get_user)

# GET /api/v1/users
# for admin use
bp.get("")(get_users)

# PUT /api/v1/users/{user_id}
bp.put("/<user_id>")(edit_user)

bp.delete("/<user_id>")(delete_user)