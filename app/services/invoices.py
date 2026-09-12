from datetime import date
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.database import commit_or_rollback
from app.exceptions import ConflictError, ValidationError
from app.extensions import db
from app.models import (
    OVERDUE_STATUS,
    Client,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
)
from app.models.mixins import utcnow
from app.validation import (
    choice_field,
    date_field,
    optional_decimal,
    optional_string,
    required_decimal,
    required_string,
)

MAX_LINE_ITEMS = 100
MAX_TAX_RATE = Decimal("100")
MIN_QUANTITY = Decimal("0.01")
MAX_QUANTITY = Decimal("100000")
MAX_UNIT_PRICE = Decimal("1000000")


# Shared by the list filter and the dashboard count so both agree, and
# kept in step with Invoice.is_overdue.
def overdue_clause():
    return and_(
        Invoice.status == InvoiceStatus.SENT.value,
        Invoice.due_date < date.today(),
    )


def _sequence_of(number, prefix):
    try:
        return int(number[len(prefix):])
    except ValueError:
        return 0


def generate_invoice_number(issue_date):
    prefix = f"INV-{issue_date.year}-"
    # Read the numbers rather than a SQL MAX, which would compare them
    # as text and break once the sequence reaches four digits.
    numbers = db.session.scalars(
        select(Invoice.number).where(Invoice.number.startswith(prefix))
    ).all()
    sequence = max(
        (_sequence_of(number, prefix) for number in numbers), default=0
    )
    return f"{prefix}{sequence + 1:03d}"


def _client_id(data, errors):
    value = data.get("client_id")
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    if isinstance(value, bool) or not isinstance(value, int):
        errors["client_id"] = "Select a client."
        return None
    if db.session.get(Client, value) is None:
        errors["client_id"] = "This client does not exist."
        return None
    return value


def _parse_line_items(data, errors):
    rows = data.get("line_items")
    if not isinstance(rows, list) or not rows:
        errors["line_items"] = "Add at least one line item."
        return []
    if len(rows) > MAX_LINE_ITEMS:
        errors["line_items"] = (
            f"An invoice cannot hold more than {MAX_LINE_ITEMS} lines."
        )
        return []

    items = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors[f"line_items[{index}]"] = "This line is not readable."
            continue

        # Errors are indexed by row so the form can point at the right one.
        row_errors = {}
        item = {
            "description": required_string(
                row, "description", 255, row_errors
            ),
            "quantity": required_decimal(
                row,
                "quantity",
                row_errors,
                minimum=MIN_QUANTITY,
                maximum=MAX_QUANTITY,
            ),
            "unit_price": required_decimal(
                row,
                "unit_price",
                row_errors,
                minimum=Decimal("0"),
                maximum=MAX_UNIT_PRICE,
            ),
        }
        for field, message in row_errors.items():
            errors[f"line_items[{index}].{field}"] = message
        if not row_errors:
            items.append(item)
    return items


def parse_invoice_payload(data):
    errors = {}
    fields = {
        "client_id": _client_id(data, errors),
        "issue_date": date_field(data, "issue_date", errors),
        "due_date": date_field(data, "due_date", errors),
        "status": choice_field(
            data,
            "status",
            InvoiceStatus.values(),
            InvoiceStatus.DRAFT.value,
            errors,
        ),
        "tax_rate": optional_decimal(
            data,
            "tax_rate",
            Decimal("0"),
            errors,
            minimum=Decimal("0"),
            maximum=MAX_TAX_RATE,
        ),
        "notes": optional_string(data, "notes", 2000, errors),
        "line_items": _parse_line_items(data, errors),
    }

    issue_date = fields["issue_date"]
    due_date = fields["due_date"]
    if issue_date and due_date and due_date < issue_date:
        errors["due_date"] = "The due date cannot precede the issue date."

    if errors:
        raise ValidationError("The invoice details are not valid.", errors)
    return fields


# The payment date only exists while the invoice is paid.
def _apply_status(invoice, status):
    invoice.status = status
    if status == InvoiceStatus.PAID.value:
        invoice.paid_at = invoice.paid_at or utcnow()
    else:
        invoice.paid_at = None


def _replace_line_items(invoice, rows):
    invoice.line_items.clear()
    for row in rows:
        invoice.line_items.append(InvoiceLineItem(**row))


def list_invoices(status=None, client_id=None, limit=None):
    statement = (
        select(Invoice)
        .options(selectinload(Invoice.client))
        .order_by(Invoice.issue_date.desc(), Invoice.id.desc())
    )
    if client_id:
        statement = statement.where(Invoice.client_id == client_id)
    if status == OVERDUE_STATUS:
        statement = statement.where(overdue_clause())
    elif status:
        statement = statement.where(Invoice.status == status)
    if limit:
        statement = statement.limit(limit)
    return db.session.scalars(statement).all()


def get_invoice(invoice_id):
    return db.get_or_404(
        Invoice, invoice_id, description="This invoice does not exist."
    )


def create_invoice(data):
    fields = parse_invoice_payload(data)
    invoice = Invoice(
        number=generate_invoice_number(fields["issue_date"]),
        client_id=fields["client_id"],
        issue_date=fields["issue_date"],
        due_date=fields["due_date"],
        tax_rate=fields["tax_rate"],
        notes=fields["notes"],
    )
    _apply_status(invoice, fields["status"])
    _replace_line_items(invoice, fields["line_items"])
    invoice.recalculate_totals()

    db.session.add(invoice)
    try:
        commit_or_rollback("create the invoice")
    except IntegrityError as error:
        # Two invoices created at the same instant can pick the same number.
        raise ConflictError(
            "That invoice number was just taken, please try again."
        ) from error
    return invoice


def update_invoice(invoice, data):
    fields = parse_invoice_payload(data)
    # The number is issued once and never rewritten, even if the issue
    # date moves to another year.
    invoice.client_id = fields["client_id"]
    invoice.issue_date = fields["issue_date"]
    invoice.due_date = fields["due_date"]
    invoice.tax_rate = fields["tax_rate"]
    invoice.notes = fields["notes"]
    _apply_status(invoice, fields["status"])
    _replace_line_items(invoice, fields["line_items"])
    invoice.recalculate_totals()

    commit_or_rollback("update the invoice")
    return invoice


def mark_invoice_paid(invoice):
    if invoice.status == InvoiceStatus.PAID.value:
        return invoice
    _apply_status(invoice, InvoiceStatus.PAID.value)
    commit_or_rollback("mark the invoice as paid")
    return invoice


def delete_invoice(invoice):
    db.session.delete(invoice)
    commit_or_rollback("delete the invoice")
