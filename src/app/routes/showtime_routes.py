from flask import Blueprint
from ..controllers.showtime_controller import (
    create_showtime,
    get_showtime,
    get_showtimes,
)

bp = Blueprint("showtime_routes", __name__, url_prefix="/showtimes")

# POST /api/v1/showtimes
bp.post("")(create_showtime)

# GET /api/v1/showtimes/<showtime_id>
bp.get("/<showtime_id>")(get_showtime)

# GET /api/v1/showtimes
bp.get("")(get_showtimes)
