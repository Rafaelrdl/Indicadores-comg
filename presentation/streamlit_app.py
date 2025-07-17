"""Streamlit application to visualize maintenance indicators."""
# ruff: noqa: E402

from __future__ import annotations

from pathlib import Path
from typing import List
import os

import streamlit as st

# Ensure the repository root is in ``sys.path`` when running via ``streamlit``
import sys

# Permite executar o app diretamente via ``streamlit run``
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from application.metrics import count_orders, orders_by_priority, percentage
from infrastructure import arkmeds_client
from domain.entities import OrderService


def ensure_login() -> bool:
    """Retrieve credentials from secrets/env and present login UI if needed."""
    try:
        secrets = st.secrets
    except FileNotFoundError:
        secrets = {}

    token = secrets.get("ARKMEDS_TOKEN") or os.getenv("ARKMEDS_TOKEN")
    email = secrets.get("ARKMEDS_EMAIL") or os.getenv("ARKMEDS_EMAIL")
    password = secrets.get("ARKMEDS_PASSWORD") or os.getenv("ARKMEDS_PASSWORD")

    if token:
        arkmeds_client.set_token(token)
    elif email:
        arkmeds_client.set_credentials(email, password or "")
    else:
        token = st.text_input("Token", type="password")
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if token:
                arkmeds_client.set_token(token)
            else:
                arkmeds_client.set_credentials(email, password)
            try:
                arkmeds_client.get_token(force=True)
                st.session_state["ark_logged"] = True
            except Exception:
                st.error("Erro de autenticação")
        return st.session_state.get("ark_logged", False)

    try:
        arkmeds_client.get_token(force=True)
    except Exception:
        return False
    return True


@st.cache_data(ttl=600)
def load_orders() -> List[OrderService]:
    """Fetch work orders from Arkmeds API."""
    # Consulta a API e converte cada item para a entidade ``OrderService``
    data = arkmeds_client.get_workorders()
    orders: List[OrderService] = []
    for item in data:
        orders.append(
            OrderService(
                tipo_servico=item.get("tipo_servico") or item.get("service_type", ""),
                estado=item.get("estado") or item.get("status", ""),
                quadro_trabalho=item.get("quadro_trabalho")
                or item.get("department", ""),
                prioridade=item.get("prioridade") or item.get("priority", ""),
                estado_tempo_atendimento=item.get("estado_tempo_atendimento")
                or item.get("time_to_attend_status"),
                estado_tempo_fechamento=item.get("estado_tempo_fechamento")
                or item.get("time_to_close_status"),
            )
        )
    return orders


def main() -> None:
    """Run Streamlit UI."""
    st.title("Indicadores de Manutenção")
    if not ensure_login():
        st.stop()

    # Obtém as ordens da API
    orders = load_orders()

    # Calcula indicadores de corretivas
    total_corretivas = count_orders(orders, tipo_servico="Manutenção Corretiva")
    total_corretivas_fechadas = count_orders(
        orders, tipo_servico="Manutenção Corretiva", estado="Fechada"
    )
    percentual_corretivas = percentage(total_corretivas_fechadas, total_corretivas)

    st.header("Ordens Corretivas")
    st.metric("Abertas", total_corretivas)
    st.metric("Fechadas", total_corretivas_fechadas)
    st.metric("% Fechadas", f"{percentual_corretivas:.2f}%")

    # Calcula indicadores de preventivas
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
    # Agrupa ordens pela prioridade definida
    priorities = orders_by_priority(orders)
    st.bar_chart(priorities)


if __name__ == "__main__":
    main()
