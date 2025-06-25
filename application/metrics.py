"""Use cases for computing maintenance indicators."""

from collections import Counter
from typing import Iterable

from domain.entities import OrderService


def count_orders(orders: Iterable[OrderService], **filters: str) -> int:
    """Count orders that match all provided filters."""
    return sum(
        1
        for o in orders
        if all(getattr(o, field) == value for field, value in filters.items())
    )


def percentage(part: int, whole: int) -> float:
    """Return percentage value with protection for division by zero."""
    return 0.0 if whole == 0 else (part / whole) * 100


def orders_by_priority(orders: Iterable[OrderService]) -> Counter:
    """Return counts of orders by priority."""
    return Counter(o.prioridade for o in orders)
