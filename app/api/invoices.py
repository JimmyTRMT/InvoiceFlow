from flask import Blueprint, jsonify, request

from app.services import invoices as invoice_service
from app.validation import get_json_body

invoices_bp = Blueprint("invoices", __name__)

MAX_LIST_LIMIT = 200


def _read_limit():
    limit = request.args.get("limit", type=int)
    if limit is None or limit < 1:
        return None
    return min(limit, MAX_LIST_LIMIT)


@invoices_bp.get("/invoices")
def list_invoices():
    invoices = invoice_service.list_invoices(
        status=request.args.get("status", "").strip().lower() or None,
        client_id=request.args.get("client_id", type=int),
        limit=_read_limit(),
    )
    # The list view drops the line items, which it never displays.
    payload = [invoice.to_dict(detailed=False) for invoice in invoices]
    return jsonify(payload), 200


@invoices_bp.post("/invoices")
def create_invoice():
    invoice = invoice_service.create_invoice(get_json_body())
    return jsonify(invoice.to_dict()), 201


@invoices_bp.get("/invoices/<int:invoice_id>")
def get_invoice(invoice_id):
    invoice = invoice_service.get_invoice(invoice_id)
    return jsonify(invoice.to_dict()), 200


@invoices_bp.put("/invoices/<int:invoice_id>")
def update_invoice(invoice_id):
    invoice = invoice_service.get_invoice(invoice_id)
    invoice_service.update_invoice(invoice, get_json_body())
    return jsonify(invoice.to_dict()), 200


@invoices_bp.post("/invoices/<int:invoice_id>/mark-paid")
def mark_invoice_paid(invoice_id):
    invoice = invoice_service.get_invoice(invoice_id)
    invoice_service.mark_invoice_paid(invoice)
    return jsonify(invoice.to_dict()), 200


@invoices_bp.delete("/invoices/<int:invoice_id>")
def delete_invoice(invoice_id):
    invoice = invoice_service.get_invoice(invoice_id)
    invoice_service.delete_invoice(invoice)
    return "", 204
