from datetime import datetime, timedelta, timezone

from flask import request, jsonify, g

from .. import db
from ..models.showtimes import Showtime
from ..models.seats import Seat
from ..models.seat_holds import SeatHold
from ..models.tickets import Ticket
from ..models.bookings import Booking
from ..models.auditorium import Auditorium
from ..models.promotions import Promotion
from ..models.movie import Movie

# responses
def _bad_request(msg, details=None, code=400):
    return (
        jsonify(
            {
                "error": {
                    "code": "BAD_REQUEST",
                    "message": msg,
                    "details": details or {},
                }
            }
        ),
        code,
    )


def _not_found(msg="Not found"):
    return (
        jsonify(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": msg,
                }
            }
        ),
        404,
    )


def _conflict(msg, details=None):
    return (
        jsonify(
            {
                "error": {
                    "code": "CONFLICT",
                    "message": msg,
                    "details": details or {},
                }
            }
        ),
        409,
    )



# Seat map for a showtime
def get_showtime_seats(showtime_id):
    """
    Return seat layout + status for a specific showtime.

    Status can be:
      - "available"
      - "held"
      - "sold"
    """
    showtime = Showtime.query.filter_by(showtime_id=showtime_id).first()
    if not showtime:
        return _not_found("Showtime not found.")

    auditorium = Auditorium.query.filter_by(
        auditorium_id=showtime.auditorium_id
    ).first()

    if not auditorium:
        return _not_found("Auditorium not found.")

    seats = (
        Seat.query.filter_by(auditorium_id=auditorium.auditorium_id)
        .order_by(Seat.seat_id)
        .all()
    )

    now = datetime.now(timezone.utc)

    sold_tickets = Ticket.query.filter_by(showtime_id=showtime_id).all()
    sold_map = {t.seat_id: True for t in sold_tickets}

    active_holds = SeatHold.query.filter(
        SeatHold.showtime_id == showtime_id,
        SeatHold.hold_expires_at > now,
    ).all()
    held_map = {h.seat_id: True for h in active_holds}

    rows_out = []
    row_count = auditorium.row_count
    col_count = auditorium.col_count

    for idx, seat in enumerate(seats):
        row_index = idx // col_count
        if row_index >= row_count:
            row_index = row_count - 1 if row_count > 0 else 0

        while len(rows_out) <= row_index:
            label = chr(ord("A") + len(rows_out))
            rows_out.append(
                {
                    "row_label": label,
                    "seats": [],
                }
            )

        status = "available"
        if seat.seat_id in sold_map:
            status = "sold"
        elif seat.seat_id in held_map:
            status = "held"

        rows_out[row_index]["seats"].append(
            {
                "seat_id": seat.seat_id,
                "seat_number": seat.seat_number,
                "status": status,
            }
        )

    return (
        jsonify(
            {
                "showtime_id": str(showtime_id),
                "auditorium": {
                    "auditorium_id": auditorium.auditorium_id,
                    "name": auditorium.name,
                    "row_count": auditorium.row_count,
                    "col_count": auditorium.col_count,
                },
                "rows": rows_out,
            }
        ),
        200,
    )



def create_booking():
    """
    Create a booking with ticket_counts.

    Request JSON:
    {
      "showtime_id": "<uuid>",
      "ticket_counts": {
        "adult": 2,
        "child": 1,
        "senior": 0
      }
    }
    """
    user = getattr(g, "current_user", None)
    if not user:
        return _bad_request("Unauthorized", code=401)

    user_id = user.user_id  # SQLAlchemy model

    data = request.get_json(silent=True) or {}
    showtime_id = data.get("showtime_id")
    ticket_counts = data.get("ticket_counts", {})

    if not showtime_id:
        return _bad_request("`showtime_id` is required.")

    if not isinstance(ticket_counts, dict):
        return _bad_request("`ticket_counts` must be an object/dict.")

    adult = int(ticket_counts.get("adult", 0) or 0)
    child = int(ticket_counts.get("child", 0) or 0)
    senior = int(ticket_counts.get("senior", 0) or 0)

    total_tickets = adult + child + senior
    if total_tickets <= 0:
        return _bad_request("You must request at least one ticket.")

    showtime = Showtime.query.filter_by(showtime_id=showtime_id).first()
    if not showtime:
        return _not_found("Showtime not found.")

    now = datetime.now(timezone.utc)
    if showtime.starts_at <= now:
        return _bad_request("Cannot create a booking for a past showtime.")

    total_cents = (
        adult * showtime.adult_price_cents
        + child * showtime.child_price_cents
        + senior * showtime.senior_price_cents
    )

    expires_at = now + timedelta(minutes=15)

    # NOTE: do not pass ticket_counts / adult_tickets / etc. to Booking
    booking = Booking(
        user_id=user_id,
        showtime_id=showtime_id,
        status="PENDING",
        total_cents=total_cents,
        created_at=now,
        expires_at=expires_at,
    )

    db.session.add(booking)
    db.session.commit()

    return (
        jsonify(
            {
                "booking_id": str(booking.booking_id),
                "user_id": str(booking.user_id),
                "showtime_id": str(booking.showtime_id),
                "status": booking.status,
                "total_cents": booking.total_cents,
                "created_at": booking.created_at.isoformat(),
                "expires_at": booking.expires_at.isoformat()
                if booking.expires_at
                else None,
                    "ticket_counts": {
                    "adult": adult,
                    "child": child,
                    "senior": senior,
                },
            }
        ),
        201,
    )



def create_seat_hold(showtime_id):
    """
    Create a temporary hold on specific seats for a showtime.

    Request JSON:
    {
      "seat_ids": [1, 2, 3],
      "hold_minutes": 5
    }
    """
    user = getattr(g, "current_user", None)
    if not user:
        return _bad_request("Unauthorized", code=401)

    user_id = user.user_id

    data = request.get_json(silent=True) or {}
    seat_ids = data.get("seat_ids")
    hold_minutes = data.get("hold_minutes", 5)

    if not isinstance(seat_ids, list) or not seat_ids:
        return _bad_request("`seat_ids` must be a non-empty list of integers.")

    try:
        seat_ids = [int(sid) for sid in seat_ids]
    except Exception:
        return _bad_request("All `seat_ids` must be integers.")

    try:
        hold_minutes = int(hold_minutes)
    except Exception:
        return _bad_request("`hold_minutes` must be an integer.")

    if hold_minutes <= 0:
        return _bad_request("`hold_minutes` must be positive.")

    showtime = Showtime.query.filter_by(showtime_id=showtime_id).first()
    if not showtime:
        return _not_found("Showtime not found.")

    now = datetime.now(timezone.utc)
    if showtime.starts_at <= now:
        return _bad_request("Cannot hold seats for a past showtime.")

    seats = Seat.query.filter(
        Seat.seat_id.in_(seat_ids),
        Seat.auditorium_id == showtime.auditorium_id,
    ).all()

    if len(seats) != len(set(seat_ids)):
        return _bad_request(
            "One or more `seat_ids` are invalid for this showtime/auditorium."
        )

    # Clear expired holds on those seats
    SeatHold.query.filter(
        SeatHold.showtime_id == showtime_id,
        SeatHold.seat_id.in_(seat_ids),
        SeatHold.hold_expires_at <= now,
    ).delete(synchronize_session=False)

    # Active holds by other users
    active_other = SeatHold.query.filter(
        SeatHold.showtime_id == showtime_id,
        SeatHold.seat_id.in_(seat_ids),
        SeatHold.hold_expires_at > now,
        SeatHold.user_id != user_id,
    ).all()

    if active_other:
        blocked = [h.seat_id for h in active_other]
        return _conflict(
            "Some seats are currently held by another user.",
            {"held_seat_ids": blocked},
        )

    # Already sold
    sold = Ticket.query.filter(
        Ticket.showtime_id == showtime_id,
        Ticket.seat_id.in_(seat_ids),
    ).all()

    if sold:
        taken_ids = [t.seat_id for t in sold]
        return _conflict(
            "Some seats are already sold.",
            {"taken_seat_ids": taken_ids},
        )

    # Remove this user's previous holds on those seats
    SeatHold.query.filter(
        SeatHold.showtime_id == showtime_id,
        SeatHold.seat_id.in_(seat_ids),
        SeatHold.user_id == user_id,
    ).delete(synchronize_session=False)

    hold_expires_at = now + timedelta(minutes=hold_minutes)
    new_holds = []
    for sid in seat_ids:
        hold = SeatHold(
            showtime_id=showtime_id,
            seat_id=sid,
            user_id=user_id,
            hold_expires_at=hold_expires_at,
        )
        db.session.add(hold)
        new_holds.append(hold)

    db.session.commit()

    return (
        jsonify(
            {
                "showtime_id": str(showtime_id),
                "user_id": str(user_id),
                "hold_expires_at": hold_expires_at.isoformat(),
                "holds": [{"seat_id": h.seat_id} for h in new_holds],
            }
        ),
        201,
    )



def checkout_booking(booking_id):
    """
    Confirm a booking and issue tickets.

    Request JSON:
    {
      "seat_ids": [1, 2, 3],
      "ticket_types": {
        "1": "adult",
        "2": "adult",
        "3": "child"
      }
    }
    """
    user = getattr(g, "current_user", None)
    if not user:
        return _bad_request("Unauthorized", code=401)

    user_id = user.user_id

    data = request.get_json(silent=True) or {}
    seat_ids = data.get("seat_ids")
    ticket_types = data.get("ticket_types", {})
    promo_code = data.get("promo_code")

    if not isinstance(seat_ids, list) or not seat_ids:
        return _bad_request("`seat_ids` must be a non-empty list of integers.")

    try:
        seat_ids = [int(sid) for sid in seat_ids]
    except Exception:
        return _bad_request("All `seat_ids` must be integers.")

    if not isinstance(ticket_types, dict):
        return _bad_request("`ticket_types` must be an object/dict.")

    booking = Booking.query.filter_by(booking_id=booking_id).first()
    if not booking:
        return _not_found("Booking not found.")

    if str(booking.user_id) != str(user_id):
        return _bad_request("Forbidden", code=403)

    now = datetime.now(timezone.utc)

    if booking.expires_at and booking.expires_at <= now:
        return _bad_request("Booking has expired.", code=400)

    if booking.status != "PENDING":
        return _bad_request(
            f"Booking is not pending (current status: {booking.status})."
        )

    showtime = Showtime.query.filter_by(showtime_id=booking.showtime_id).first()
    if not showtime:
        return _not_found("Showtime not found for this booking.")

    # Derive counts + recompute total from payload and compare to booking.total_cents
    counts_from_payload = {"adult": 0, "child": 0, "senior": 0}
    for sid in seat_ids:
        ttype = ticket_types.get(str(sid))
        if ttype not in ("adult", "child", "senior"):
            return _bad_request(
                "Each seat must have a valid ticket type: 'adult', 'child', or 'senior'."
            )
        counts_from_payload[ttype] += 1

    new_total = (
        counts_from_payload["adult"] * showtime.adult_price_cents
        + counts_from_payload["child"] * showtime.child_price_cents
        + counts_from_payload["senior"] * showtime.senior_price_cents
    )

    if new_total != booking.total_cents:
        return _bad_request(
            "Ticket types / quantities do not match the original booking total.",
            {
                "original_total_cents": booking.total_cents,
                "new_total_cents": new_total,
                "ticket_counts": counts_from_payload,
            },
        )
    
    if promo_code:
        promotion = Promotion.query.filter_by(code=promo_code, is_active=True).first()
        if promotion:
            discount_cents = int(new_total * float(promotion.discount_percent) / 100)
            booking.total_cents -= discount_cents

    # Check active holds for this user
    active_holds = SeatHold.query.filter(
        SeatHold.showtime_id == booking.showtime_id,
        SeatHold.seat_id.in_(seat_ids),
        SeatHold.user_id == user_id,
        SeatHold.hold_expires_at > now,
    ).all()

    if len(active_holds) != len(set(seat_ids)):
        held_ids = {h.seat_id for h in active_holds}
        missing = [sid for sid in seat_ids if sid not in held_ids]
        return _bad_request(
            "You must hold all seats before checkout.",
            {"missing_holds_for_seat_ids": missing},
        )

    # Ensure seats not already sold
    sold = Ticket.query.filter(
        Ticket.showtime_id == booking.showtime_id,
        Ticket.seat_id.in_(seat_ids),
    ).all()

    if sold:
        taken_ids = [t.seat_id for t in sold]
        return _conflict(
            "Some seats are already sold.",
            {"taken_seat_ids": taken_ids},
        )

    # Issue tickets
    tickets = []
    for sid in seat_ids:
        ttype = ticket_types[str(sid)]
        if ttype == "adult":
            price_cents = showtime.adult_price_cents
        elif ttype == "child":
            price_cents = showtime.child_price_cents
        else:
            price_cents = showtime.senior_price_cents

        ticket = Ticket(
            booking_id=booking.booking_id,
            showtime_id=booking.showtime_id,
            seat_id=sid,
            ticket_type=ttype,
            price_cents=price_cents,
            created_at=now,
        )
        db.session.add(ticket)
        tickets.append(ticket)

    booking.status = "CONFIRMED"
    booking.expires_at = None

    SeatHold.query.filter(
        SeatHold.showtime_id == booking.showtime_id,
        SeatHold.seat_id.in_(seat_ids),
        SeatHold.user_id == user_id,
    ).delete(synchronize_session=False)

    db.session.commit()

    return (
        jsonify(
            {
                "booking_id": str(booking.booking_id),
                "status": booking.status,
                "showtime_id": str(booking.showtime_id),
                "user_id": str(booking.user_id),
                "total_cents": booking.total_cents,
                "ticket_counts": counts_from_payload,
                "tickets": [
                    {
                        "ticket_id": str(t.ticket_id),
                        "seat_id": t.seat_id,
                        "ticket_type": t.ticket_type,
                        "price_cents": t.price_cents,
                    }
                    for t in tickets
                ],
            }
        ),
        200,
    )

# ---------------------------------------------------------------------------
# Getting past bookings for the current user.
# ---------------------------------------------------------------------------

def get_user_bookings():
    user = getattr(g, "current_user", None)
    if not user:
        return _bad_request("Unauthorized", code=401)
    
    bookings = Booking.query.filter_by(
        user_id=user.user_id,
        status="CONFIRMED"  
    ).order_by(Booking.created_at.desc()).all()

    result = []
    for booking in bookings:
        showtime = Showtime.query.filter_by(showtime_id=booking.showtime_id).first()
        movie = Movie.query.filter_by(movie_id=showtime.movie_id).first() 
        ticket_count = Ticket.query.filter_by(booking_id=booking.booking_id).count()

        result.append({
            "booking_id": str(booking.booking_id),
            "order_date": booking.created_at.isoformat(),
            "total_cents": booking.total_cents,
            "ticket_count": ticket_count,
            "movie": {
                "title": movie.title,
                "film_rating_code": movie.film_rating_code,
            },
            "showtime": {
                "starts_at": showtime.starts_at.isoformat(),
            },
        })
    return jsonify({"data": result}), 200