"""Aggregated figures shown on the dashboard."""

from datetime import date, datetime, time

from sqlalchemy import and_, case, func, select

from app.extensions import db
from app.models import Invoice, InvoiceStatus
from app.services.invoices import overdue_clause


def _month_bounds(today):
    """Return the first instant of this month and of the next one."""
    start = today.replace(day=1)
    if start.month == 12:
        next_start = start.replace(year=start.year + 1, month=1)
    else:
        next_start = start.replace(month=start.month + 1)
    return datetime.combine(start, time.min), datetime.combine(
        next_start, time.min
    )


def _amount_when(condition):
    """Sum the invoice totals that match a condition, zero otherwise."""
    return func.coalesce(
        func.sum(case((condition, Invoice.total), else_=0)), 0
    )


def _count_when(condition):
    """Count the invoices that match a condition."""
    return func.coalesce(func.sum(case((condition, 1), else_=0)), 0)


def get_dashboard_stats():
    """Compute the dashboard figures in one aggregate query."""
    today = date.today()
    month_start, next_month_start = _month_bounds(today)

    unpaid = Invoice.status != InvoiceStatus.PAID.value
    # Payment dates are stored in UTC while the month comes from the
    # local calendar, which can only shift a payment made within hours
    # of a month boundary.
    cashed_this_month = and_(
        Invoice.status == InvoiceStatus.PAID.value,
        Invoice.paid_at >= month_start,
        Invoice.paid_at < next_month_start,
    )

    row = db.session.execute(
        select(
            _amount_when(unpaid).label("outstanding_total"),
            _amount_when(cashed_this_month).label("paid_this_month"),
            _count_when(overdue_clause()).label("overdue_count"),
        )
    ).one()

    return {
        "outstanding_total": float(row.outstanding_total),
        "paid_this_month": float(row.paid_this_month),
        "overdue_count": int(row.overdue_count),
        "month": today.strftime("%Y-%m"),
    }
