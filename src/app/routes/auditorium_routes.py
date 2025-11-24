from flask import Blueprint
from ..controllers import auditorium_controller
from ..middleware.auth import require_auth  # or require_admin if you have it

bp = Blueprint("auditorium_routes", __name__, url_prefix="/auditoriums")


# CREATE auditorium (admin-only)
@bp.post("")
def create_auditorium_route():
    return auditorium_controller.create_auditorium()


# LIST auditoriums
@bp.get("")
def get_auditoriums_route():
    return auditorium_controller.get_auditoriums()


# GET one auditorium (optionally include seats via ?include_seats=1)
@bp.get("/<int:auditorium_id>")
def get_auditorium_route(auditorium_id):
    return auditorium_controller.get_auditorium(auditorium_id)


# UPDATE auditorium (name only; admin-only)
@bp.patch("/<int:auditorium_id>")
def update_auditorium_route(auditorium_id):
    return auditorium_controller.update_auditorium(auditorium_id)


# DELETE auditorium (admin-only)
@bp.delete("/<int:auditorium_id>")
def delete_auditorium_route(auditorium_id):
    return auditorium_controller.delete_auditorium(auditorium_id)
