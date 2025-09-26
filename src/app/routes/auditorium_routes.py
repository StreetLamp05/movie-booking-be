from flask import Blueprint
from ..controllers.auditorium_controller import (
    create_auditorium,
    get_auditoriums,
    get_auditorium,
)


bp = Blueprint("auditorium_routes", __name__, url_prefix="/auditorium")

# POST /api/v1/auditorium
bp.post("")(create_auditorium)

# GET /api/v1/auditorium
bp.get("")(get_auditoriums)

# GET /api/v1/auditorium/<auditorium_id>
bp.get("/<int:auditorium_id>")(get_auditorium)
