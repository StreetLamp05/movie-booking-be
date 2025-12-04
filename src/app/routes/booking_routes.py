from flask import Blueprint

from ..middleware.auth import require_auth
from ..controllers import booking_controller

bp = Blueprint("bookings", __name__, url_prefix="/bookings")


@bp.get("/saved-cards")
@require_auth
def get_saved_cards_route():
    return booking_controller.get_saved_cards()

@bp.post("")
@require_auth
def create_booking_route():
    return booking_controller.create_booking()


@bp.post("/<booking_id>/checkout")
@require_auth
def checkout_booking_route(booking_id):
    return booking_controller.checkout_booking(booking_id)

@bp.get("/history")
@require_auth
def get_order_history_route():
    return booking_controller.get_user_bookings()