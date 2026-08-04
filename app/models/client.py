"""Client model: whoever an invoice is addressed to."""

from app.extensions import db
from app.models.mixins import TimestampMixin, to_iso


class Client(db.Model, TimestampMixin):
    """A customer of the freelancer.

    Only the name and the email are mandatory: the postal address is
    often unknown when a client is first added and filled in later.
    """

    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(120))
    address = db.Column(db.Text)

    # No delete cascade on purpose: invoices are an accounting record and
    # must never disappear because a client row was removed.
    invoices = db.relationship("Invoice", back_populates="client")

    def summary(self):
        """Return the short form embedded in invoice payloads."""
        return {
            "id": self.id,
            "name": self.name,
            "company": self.company,
        }

    def to_dict(self):
        """Serialise the client for the JSON API."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "address": self.address,
            "created_at": to_iso(self.created_at),
            "updated_at": to_iso(self.updated_at),
        }

    def __repr__(self):
        """Readable form used in the shell and in log messages."""
        return f"<Client {self.id} {self.name!r}>"
