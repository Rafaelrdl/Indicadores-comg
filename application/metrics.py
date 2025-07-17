"""Use cases for computing maintenance indicators."""

from collections import Counter
from typing import Iterable

from domain.entities import OrderService


def count_orders(orders: Iterable[OrderService], **filters: str) -> int:
    """Count orders that match all provided filters.

    Args:
        orders: Lista de ordens de serviço a serem filtradas.
        **filters: Pares campo=valor usados como filtro.

    Returns:
        Número de ordens que atendem a todos os filtros fornecidos.
    """
    return sum(
        1
        for o in orders
        # ``all`` garante que todos os filtros sejam satisfeitos
        if all(getattr(o, field) == value for field, value in filters.items())
    )


def percentage(part: int, whole: int) -> float:
    """Calculate a percentage value.

    Args:
        part: Valor da parte.
        whole: Valor do todo.

    Returns:
        Percentual correspondente ou ``0.0`` quando ``whole`` é ``0``.
    """
    # Evita divisão por zero quando ``whole`` é zero
    return 0.0 if whole == 0 else (part / whole) * 100


def orders_by_priority(orders: Iterable[OrderService]) -> Counter:
    """Count orders grouped by priority.

    Args:
        orders: Lista de ordens a serem agrupadas.

    Returns:
        ``Counter`` com a quantidade de ordens por prioridade.
    """
    # ``Counter`` facilita a contagem de itens repetidos em uma única etapa
    return Counter(o.prioridade for o in orders)
