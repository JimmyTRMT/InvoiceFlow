"""Page routes that serve the frontend shell."""

from flask import Blueprint, current_app, render_template

from app.services.invoices import get_invoice

web_bp = Blueprint("web", __name__)


@web_bp.app_context_processor
def inject_settings():
    """Expose the display settings every template needs."""
    return {
        "currency": current_app.config["CURRENCY"],
        "business": {
            "name": current_app.config["BUSINESS_NAME"],
            "email": current_app.config["BUSINESS_EMAIL"],
            "address": current_app.config["BUSINESS_ADDRESS"],
        },
    }


@web_bp.get("/")
def dashboard():
    """Render the dashboard page."""
    return render_template("dashboard.html")


@web_bp.get("/clients")
def clients():
    """Render the client management page."""
    return render_template("clients.html")


@web_bp.get("/invoices/new")
def new_invoice():
    """Render the invoice creation page."""
    return render_template("invoice_form.html")


@web_bp.get("/invoices/<int:invoice_id>")
def invoice_detail(invoice_id):
    """Render the printable page of a single invoice, or a 404 page."""
    invoice = get_invoice(invoice_id)
    return render_template("invoice_detail.html", invoice_id=invoice.id)
