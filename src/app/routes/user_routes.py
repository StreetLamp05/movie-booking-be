from flask import Blueprint
from ..controllers.user_controller import (
    get_user_profile,
    update_user_profile,
    get_user_cards,
    add_user_card,
    delete_user_card
)

bp = Blueprint("user_routes", __name__, url_prefix="/users")

# Profile routes
# GET /api/v1/users/profile
bp.get("/profile")(get_user_profile)
# POST /api/v1/users/profile
bp.put("/profile")(update_user_profile)

# Card Routes
# GET /api/v1/users/cards
bp.get("/cards")(get_user_cards)
# POST  /api/v1/users/cards
bp.post("/cards")(add_user_card)
# DELETE /api/v1/users/cards/<card_id>
bp.delete("/cards/<card_id>")(delete_user_card)