from app.extensions import db
from app.models.mixins import TimestampMixin, to_iso


class Client(db.Model, TimestampMixin):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(120))
    address = db.Column(db.Text)

    # No delete cascade: invoices are an accounting record and must not
    # disappear with the client row.
    invoices = db.relationship("Invoice", back_populates="client")

    # Short form embedded in invoice payloads.
    def summary(self):
        return {
            "id": self.id,
            "name": self.name,
            "company": self.company,
        }

    def to_dict(self):
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
        return f"<Client {self.id} {self.name!r}>"
