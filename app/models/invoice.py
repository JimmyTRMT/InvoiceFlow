"""Invoice model and the statuses an invoice can hold."""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from app.extensions import db
from app.models.mixins import TimestampMixin, to_iso
from app.models.types import TWO_PLACES, ExactDecimal

OVERDUE_STATUS = "overdue"


class InvoiceStatus(str, Enum):
    """The statuses a user is allowed to store on an invoice.

    "overdue" is deliberately missing: it is derived from the due date by
    Invoice.effective_status, so it cannot drift out of date the way a
    stored flag would.
    """

    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"

    @classmethod
    def values(cls):
        """List the accepted column values."""
        return [status.value for status in cls]


def _status_check_constraint():
    """Build the CHECK constraint that guards the status column.

    Generating it from the enum keeps the database and the Python code
    from drifting apart when a status is added.
    """
    allowed = ", ".join(f"'{value}'" for value in InvoiceStatus.values())
    return db.CheckConstraint(
        f"status IN ({allowed})", name="ck_invoices_status"
    )


class Invoice(db.Model, TimestampMixin):
    """An invoice, its client, its line items and its amounts.

    The totals are stored instead of being recomputed on every read
    because the dashboard aggregates them directly in SQL. Every write
    path calls recalculate_totals, so the stored amounts can never
    disagree with the line items.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        _status_check_constraint(),
        db.CheckConstraint("tax_rate >= 0", name="ck_invoices_tax_rate"),
    )

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False, unique=True)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id"),
        nullable=False,
        index=True,
    )
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(
        db.String(16),
        nullable=False,
        default=InvoiceStatus.DRAFT.value,
        index=True,
    )
    tax_rate = db.Column(
        ExactDecimal(2), nullable=False, default=Decimal("0")
    )
    notes = db.Column(db.Text)

    # Kept separately from the status so the dashboard can aggregate what
    # was actually cashed in during a given month.
    paid_at = db.Column(db.DateTime)

    subtotal = db.Column(
        ExactDecimal(2), nullable=False, default=Decimal("0")
    )
    tax_amount = db.Column(
        ExactDecimal(2), nullable=False, default=Decimal("0")
    )
    total = db.Column(ExactDecimal(2), nullable=False, default=Decimal("0"))

    client = db.relationship("Client", back_populates="invoices")
    line_items = db.relationship(
        "InvoiceLineItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceLineItem.id",
    )

    @property
    def is_overdue(self):
        """Tell whether the invoice is unpaid and past its due date."""
        if self.status == InvoiceStatus.PAID.value:
            return False
        return self.due_date is not None and self.due_date < date.today()

    @property
    def effective_status(self):
        """Return the status shown to the user, overdue included."""
        return OVERDUE_STATUS if self.is_overdue else self.status

    def recalculate_totals(self):
        """Recompute the subtotal, the tax and the grand total.

        The client sends line items, never amounts, so this is the only
        place where an invoice decides what it is worth.
        """
        subtotal = Decimal("0")
        for item in self.line_items:
            subtotal += item.line_total

        rate = self.tax_rate or Decimal("0")
        self.subtotal = subtotal.quantize(TWO_PLACES)
        self.tax_amount = (self.subtotal * rate / Decimal("100")).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
        self.total = self.subtotal + self.tax_amount

    def to_dict(self, include_line_items=True):
        """Serialise the invoice for the JSON API.

        List views skip the line items, which keeps the dashboard payload
        small when an invoice carries a long breakdown.
        """
        payload = {
            "id": self.id,
            "number": self.number,
            "client_id": self.client_id,
            "client": self.client.summary() if self.client else None,
            "issue_date": to_iso(self.issue_date),
            "due_date": to_iso(self.due_date),
            "status": self.status,
            "effective_status": self.effective_status,
            "is_overdue": self.is_overdue,
            "tax_rate": float(self.tax_rate),
            "subtotal": float(self.subtotal),
            "tax_amount": float(self.tax_amount),
            "total": float(self.total),
            "notes": self.notes,
            "paid_at": to_iso(self.paid_at),
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
        }
        if include_line_items:
            payload["line_items"] = [
                item.to_dict() for item in self.line_items
            ]
        return payload

    def __repr__(self):
        """Readable form used in the shell and in log messages."""
        return f"<Invoice {self.number} {self.status}>"
