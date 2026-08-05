"""Client endpoints."""

from flask import Blueprint, jsonify, request

from app.services import clients as client_service
from app.validation import get_json_body

clients_bp = Blueprint("clients", __name__)

# Long enough for a company name, short enough to stay a search box.
MAX_SEARCH_LENGTH = 100


@clients_bp.get("/clients")
def list_clients():
    """Return every client, optionally filtered by a search term."""
    search = request.args.get("search", "").strip()[:MAX_SEARCH_LENGTH]
    clients = client_service.list_clients(search or None)
    return jsonify([client.to_dict() for client in clients]), 200


@clients_bp.post("/clients")
def create_client():
    """Create a client and return it with its generated id."""
    client = client_service.create_client(get_json_body())
    return jsonify(client.to_dict()), 201


@clients_bp.get("/clients/<int:client_id>")
def get_client(client_id):
    """Return a single client."""
    client = client_service.get_client(client_id)
    return jsonify(client.to_dict()), 200


@clients_bp.put("/clients/<int:client_id>")
def update_client(client_id):
    """Replace the details of an existing client."""
    client = client_service.get_client(client_id)
    client_service.update_client(client, get_json_body())
    return jsonify(client.to_dict()), 200


@clients_bp.delete("/clients/<int:client_id>")
def delete_client(client_id):
    """Delete a client that has no invoice attached to it."""
    client = client_service.get_client(client_id)
    client_service.delete_client(client)
    return "", 204
