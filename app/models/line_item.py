from decimal import ROUND_HALF_UP

from app.extensions import db
from app.models.types import TWO_PLACES, ExactDecimal


class InvoiceLineItem(db.Model):
    __tablename__ = "invoice_line_items"
    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="ck_line_items_quantity"),
        db.CheckConstraint(
            "unit_price >= 0", name="ck_line_items_unit_price"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(ExactDecimal(2), nullable=False)
    unit_price = db.Column(ExactDecimal(2), nullable=False)

    invoice = db.relationship("Invoice", back_populates="line_items")

    # Rounded here so the invoice total is the sum of what is displayed.
    @property
    def line_total(self):
        return (self.quantity * self.unit_price).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "quantity": float(self.quantity),
            "unit_price": float(self.unit_price),
            "line_total": float(self.line_total),
        }

    def __repr__(self):
        return f"<InvoiceLineItem {self.id} {self.description!r}>"
