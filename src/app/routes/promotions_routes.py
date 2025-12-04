from flask import Blueprint

from ..controllers import promotions_controller

bp = Blueprint("promotions", __name__, url_prefix="/promotions")

@bp.post("/validate")
def validate_promo_route():
    return promotions_controller.validate_promo_code()