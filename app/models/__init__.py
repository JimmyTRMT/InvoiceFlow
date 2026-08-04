"""Database models.

Importing this package registers every table on the SQLAlchemy metadata,
which is what create_all needs in order to build the schema.
"""

from app.models.client import Client
from app.models.invoice import OVERDUE_STATUS, Invoice, InvoiceStatus
from app.models.line_item import InvoiceLineItem

__all__ = [
    "Client",
    "Invoice",
    "InvoiceLineItem",
    "InvoiceStatus",
    "OVERDUE_STATUS",
]
