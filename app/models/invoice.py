from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from app.extensions import db
from app.models.mixins import TimestampMixin, to_iso
from app.models.types import TWO_PLACES, ExactDecimal

OVERDUE_STATUS = "overdue"


# Only these three are stored; overdue is derived from the due date.
class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"

    @classmethod
    def values(cls):
        return [status.value for status in cls]


def _status_check_constraint():
    allowed = ", ".join(f"'{value}'" for value in InvoiceStatus.values())
    return db.CheckConstraint(
        f"status IN ({allowed})", name="ck_invoices_status"
    )


class Invoice(db.Model, TimestampMixin):
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

    # Kept apart from the status so the dashboard can aggregate by month.
    paid_at = db.Column(db.DateTime)

    # Stored rather than derived because the dashboard sums them in SQL,
    # and always rewritten by recalculate_totals.
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

    # A draft never reached the client, so it cannot be late.
    @property
    def is_overdue(self):
        if self.status != InvoiceStatus.SENT.value:
            return False
        return self.due_date is not None and self.due_date < date.today()

    @property
    def effective_status(self):
        return OVERDUE_STATUS if self.is_overdue else self.status

    def recalculate_totals(self):
        subtotal = Decimal("0")
        for item in self.line_items:
            subtotal += item.line_total

        rate = self.tax_rate or Decimal("0")
        self.subtotal = subtotal.quantize(TWO_PLACES)
        self.tax_amount = (self.subtotal * rate / Decimal("100")).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
        self.total = self.subtotal + self.tax_amount

    def to_dict(self, detailed=True):
        payload = {
            "id": self.id,
            "number": self.number,
            "client_id": self.client_id,
            "client": self._client_payload(detailed),
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
        if detailed:
            payload["line_items"] = [
                item.to_dict() for item in self.line_items
            ]
        return payload

    # The full client is only worth sending when the invoice is read alone.
    def _client_payload(self, detailed):
        if self.client is None:
            return None
        return self.client.to_dict() if detailed else self.client.summary()

    def __repr__(self):
        return f"<Invoice {self.number} {self.status}>"
