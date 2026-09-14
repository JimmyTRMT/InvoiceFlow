from flask import Blueprint, current_app, render_template

from app.services.invoices import get_invoice

web_bp = Blueprint("web", __name__)


# Display settings every template reads, injected once for all of them.
@web_bp.app_context_processor
def inject_settings():
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
    return render_template("dashboard.html")


@web_bp.get("/clients")
def clients():
    return render_template("clients.html")


@web_bp.get("/invoices")
def invoice_list():
    return render_template("invoices.html")


@web_bp.get("/invoices/new")
def new_invoice():
    return render_template("invoice_form.html", invoice_id=None)


# Loaded server side so an unknown id renders the 404 page, not an
# empty sheet that only fails once the script runs.
@web_bp.get("/invoices/<int:invoice_id>")
def invoice_detail(invoice_id):
    invoice = get_invoice(invoice_id)
    return render_template("invoice_detail.html", invoice_id=invoice.id)


# The same form serves both, told apart by the id it is given.
@web_bp.get("/invoices/<int:invoice_id>/edit")
def edit_invoice(invoice_id):
    invoice = get_invoice(invoice_id)
    return render_template(
        "invoice_form.html", invoice_id=invoice.id, number=invoice.number
    )
