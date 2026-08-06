"""Page routes that serve the frontend shell."""

from flask import Blueprint, current_app, render_template

web_bp = Blueprint("web", __name__)


@web_bp.app_context_processor
def inject_currency():
    """Expose the configured currency to every template."""
    return {"currency": current_app.config["CURRENCY"]}


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
