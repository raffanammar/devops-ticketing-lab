from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models.ticket import Ticket

tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json(silent=True) or {}
    title = data.get("title")

    if not title:
        return jsonify({"error": "field 'title' is required"}), 400

    ticket = Ticket(
        title=title,
        description=data.get("description"),
        status=data.get("status", "open"),
    )
    db.session.add(ticket)
    db.session.commit()

    return jsonify(ticket.to_dict()), 201


@tickets_bp.route("/tickets", methods=["GET"])
def list_tickets():
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tickets]), 200
