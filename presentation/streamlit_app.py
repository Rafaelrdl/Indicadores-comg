"""Streamlit application to visualize maintenance indicators."""
# ruff: noqa: E402

from __future__ import annotations

from pathlib import Path
from typing import List

import streamlit as st

# Ensure the repository root is in ``sys.path`` when running via ``streamlit``
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from application.metrics import count_orders, orders_by_priority, percentage
from infrastructure.xls_repository import OrderServiceXLSRepository
from domain.entities import OrderService


DATA_FILE = Path("data/ordens_servico.xls")


def load_orders() -> List[OrderService]:
    """Load orders from the XLS file configured in ``DATA_FILE``.

    Returns:
        Lista de :class:`OrderService` carregadas do disco.
    """
    repo = OrderServiceXLSRepository(DATA_FILE)
    return repo.load()


def main() -> None:
    """Run Streamlit UI."""
    st.title("Indicadores de Manutenção")
    orders = load_orders()

    total_corretivas = count_orders(orders, tipo_servico="Manutenção Corretiva")
    total_corretivas_fechadas = count_orders(
        orders, tipo_servico="Manutenção Corretiva", estado="Fechada"
    )
    percentual_corretivas = percentage(total_corretivas_fechadas, total_corretivas)

    st.header("Ordens Corretivas")
    st.metric("Abertas", total_corretivas)
    st.metric("Fechadas", total_corretivas_fechadas)
    st.metric("% Fechadas", f"{percentual_corretivas:.2f}%")

    total_preventivas = count_orders(orders, tipo_servico="Manutenção Preventiva")
    total_preventivas_fechadas = count_orders(
        orders, tipo_servico="Manutenção Preventiva", estado="Fechada"
    )
    percentual_preventivas = percentage(total_preventivas_fechadas, total_preventivas)

    st.header("Ordens Preventivas")
    st.metric("Abertas", total_preventivas)
    st.metric("Fechadas", total_preventivas_fechadas)
    st.metric("% Fechadas", f"{percentual_preventivas:.2f}%")

    st.header("Prioridades")
    priorities = orders_by_priority(orders)
    st.bar_chart(priorities)


if __name__ == "__main__":
    main()
