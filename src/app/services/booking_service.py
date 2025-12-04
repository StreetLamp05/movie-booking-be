from flask import jsonify
from ..models import Booking, Showtime, User, Seat, SeatHold
from .. import db


def create_booking(data):
    """Create a new booking for a user"""
    try:
        user_id = data.get('user_id')
        showtime_id = data.get('showtime_id')
        seat_ids = data.get('seat_ids', [])
        
        if not user_id or not showtime_id:
            return jsonify({"error": "Missing required fields"}), 400
        
        # Verify user and showtime exist
        user = User.query.get(user_id)
        showtime = Showtime.query.get(showtime_id)
        
        if not user or not showtime:
            return jsonify({"error": "User or showtime not found"}), 404
        
        # Create booking
        booking = Booking(
            user_id=user_id,
            showtime_id=showtime_id,
            status="PENDING"
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            "booking_id": str(booking.booking_id),
            "status": booking.status,
            "created_at": booking.created_at
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def checkout_booking(booking_id, data):
    """Checkout/process a booking"""
    try:
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
        
        if booking.status != "PENDING":
            return jsonify({"error": f"Cannot checkout booking with status {booking.status}"}), 400
        
        # Process payment, update booking status
        booking.status = "CONFIRMED"
        db.session.commit()
        
        return jsonify({
            "booking_id": str(booking.booking_id),
            "status": booking.status,
            "total_cents": booking.total_cents
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def get_showtime_seats(showtime_id):
    """Get available seats for a showtime"""
    try:
        showtime = Showtime.query.get(showtime_id)
        
        if not showtime:
            return jsonify({"error": "Showtime not found"}), 404
        
        # Get all seats for the auditorium
        seats = Seat.query.filter_by(auditorium_id=showtime.auditorium_id).all()
        
        # Get booked seat IDs
        booked_seats = db.session.query(Ticket.seat_id).filter(
            Ticket.booking_id.in_(
                db.session.query(Booking.booking_id).filter_by(
                    showtime_id=showtime_id,
                    status="CONFIRMED"
                )
            )
        ).all()
        booked_seat_ids = {str(s[0]) for s in booked_seats}
        
        seats_data = []
        for seat in seats:
            seats_data.append({
                "seat_id": str(seat.seat_id),
                "row": seat.row,
                "col": seat.col,
                "available": str(seat.seat_id) not in booked_seat_ids
            })
        
        return jsonify({"seats": seats_data}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_seat_hold(showtime_id, data):
    """Create a seat hold for a showtime"""
    try:
        user_id = data.get('user_id')
        seat_ids = data.get('seat_ids', [])
        
        if not user_id or not seat_ids:
            return jsonify({"error": "Missing required fields"}), 400
        
        showtime = Showtime.query.get(showtime_id)
        if not showtime:
            return jsonify({"error": "Showtime not found"}), 404
        
        # Create seat holds
        holds = []
        for seat_id in seat_ids:
            hold = SeatHold(
                user_id=user_id,
                seat_id=seat_id,
                showtime_id=showtime_id
            )
            holds.append(hold)
            db.session.add(hold)
        
        db.session.commit()
        
        return jsonify({
            "holds": [{"seat_id": str(h.seat_id)} for h in holds]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
