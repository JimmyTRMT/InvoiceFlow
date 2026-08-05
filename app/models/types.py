"""Column types that keep decimal values exact in SQLite."""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Integer
from sqlalchemy.types import TypeDecorator

TWO_PLACES = Decimal("0.01")


class ExactDecimal(TypeDecorator):
    """A decimal stored as a scaled integer, free of float rounding."""

    impl = Integer
    cache_ok = True

    def __init__(self, scale=2, **kwargs):
        """Configure how many decimal places the column keeps."""
        super().__init__(**kwargs)
        self.scale = scale
        self._quantum = Decimal(1).scaleb(-scale)
        self._factor = Decimal(10) ** scale

    def process_bind_param(self, value, dialect):
        """Convert a Python number into the stored integer."""
        if value is None:
            return None
        amount = Decimal(str(value)).quantize(
            self._quantum, rounding=ROUND_HALF_UP
        )
        return int(amount * self._factor)

    def process_result_value(self, value, dialect):
        """Rebuild the Decimal from the stored integer."""
        if value is None:
            return None
        return (Decimal(value) / self._factor).quantize(self._quantum)
