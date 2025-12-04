from flask import Blueprint

from ..controllers import showtime_controller
from ..controllers import booking_controller  # for /<showtime_id>/seats
from ..middleware.auth import require_auth

bp = Blueprint("showtimes", __name__, url_prefix="/showtimes")


# GET /api/v1/showtimes
# supports query params: movie_id, from, to, limit, offset, sort
@bp.get("")
def get_showtimes_route():
    return showtime_controller.get_showtimes()


# GET /api/v1/showtimes/<showtime_id>/seats
@bp.get("/<showtime_id>/seats")
@require_auth
def get_showtime_seats_route(showtime_id):
    # reuse the function we put in booking_controller
    return booking_controller.get_showtime_seats(showtime_id)

@bp.post("/<showtime_id>/hold")
@require_auth
def hold_seats_route(showtime_id):
    return booking_controller.create_seat_hold(showtime_id)