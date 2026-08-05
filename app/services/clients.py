"""Business rules for the client resource."""

from sqlalchemy import func, or_, select

from app.database import commit_or_rollback
from app.exceptions import ConflictError, ValidationError
from app.extensions import db
from app.models import Client, Invoice
from app.validation import email_address, optional_string, required_string


def parse_client_payload(data):
    """Turn a request body into validated client fields."""
    errors = {}
    fields = {
        "name": required_string(data, "name", 120, errors),
        "email": email_address(data, "email", errors),
        "company": optional_string(data, "company", 120, errors),
        "address": optional_string(data, "address", 500, errors),
    }
    if errors:
        raise ValidationError("The client details are not valid.", errors)
    return fields


def list_clients(search=None):
    """Return the clients sorted by name, optionally filtered."""
    statement = select(Client).order_by(Client.name.asc())
    if search:
        # SQLAlchemy binds the pattern, so the term cannot inject SQL.
        pattern = f"%{search}%"
        statement = statement.where(
            or_(
                Client.name.ilike(pattern),
                Client.company.ilike(pattern),
                Client.email.ilike(pattern),
            )
        )
    return db.session.scalars(statement).all()


def get_client(client_id):
    """Return a client, or raise a 404 if the id does not exist."""
    return db.get_or_404(
        Client, client_id, description="This client does not exist."
    )


def create_client(data):
    """Create a client from a request body."""
    client = Client(**parse_client_payload(data))
    db.session.add(client)
    commit_or_rollback("create the client")
    return client


def update_client(client, data):
    """Replace the details of an existing client."""
    for field, value in parse_client_payload(data).items():
        setattr(client, field, value)
    commit_or_rollback("update the client")
    return client


def delete_client(client):
    """Delete a client, unless invoices still point at it."""
    invoice_count = db.session.scalar(
        select(func.count(Invoice.id)).where(Invoice.client_id == client.id)
    )
    if invoice_count:
        raise ConflictError(
            f"This client still has {invoice_count} invoice(s) and "
            "cannot be deleted."
        )

    db.session.delete(client)
    commit_or_rollback("delete the client")
