from flask import Blueprint
from ..controllers.user_controller import (
    get_user_profile,
    update_user_profile,
    get_user_cards,
    add_user_card,
    delete_user_card,
    update_user_card,
)

bp = Blueprint("user_routes", __name__, url_prefix="/users")

# Profile
bp.get("/profile")(get_user_profile)
bp.put("/profile")(update_user_profile)

# Cards
bp.get("/cards")(get_user_cards)
bp.post("/cards")(add_user_card)
bp.patch("/cards/<card_id>")(update_user_card)
bp.delete("/cards/<card_id>")(delete_user_card)
