"""Filtros específicos para a página de Ordem de Serviço."""
from __future__ import annotations

import time
from datetime import date

import streamlit as st

from arkmeds_client.client import ArkmedsClient

from .utils import run_async_safe


@st.cache_data(ttl=86400)
def _get_estados_os(_client: ArkmedsClient) -> list[dict]:
    """Busca lista de estados disponíveis para filtros de OS."""
    return run_async_safe(_client.list_estados())


def render_os_filters(client: ArkmedsClient) -> dict:
    """Renderiza filtros específicos para Ordem de Serviço na sidebar.
    
    Args:
        client: Cliente Arkmeds configurado
        
    Returns:
        Dict com filtros selecionados: dt_ini, dt_fim, estado_ids
    """
    st.sidebar.markdown("### 🔍 Filtros de Ordem de Serviço")

    # Initialize session state for OS filters if not exists
    if "os_filters" not in st.session_state:
        st.session_state["os_filters"] = {
            "dt_ini": date.today().replace(day=1),  # Primeiro dia do mês atual
            "dt_fim": date.today(),  # Hoje
            "estado_ids": [],  # Todos os estados
        }
        st.session_state["os_filters_version"] = 0

    state = st.session_state.get("os_filters", {})

    # Load estados data
    start = time.time()
    try:
        estados = _get_estados_os(client)
        if time.time() - start > 1:
            st.sidebar.warning("⏳ Carregando opções de filtro...")
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar estados: {e!s}")
        estados = []

    # Date filters
    st.sidebar.markdown("#### 📅 Período")
    dt_ini = st.sidebar.date_input(
        "Data início",
        value=state.get("dt_ini", date.today().replace(day=1)),
        key="os_dt_ini"
    )
    dt_fim = st.sidebar.date_input(
        "Data fim",
        value=state.get("dt_fim", date.today()),
        key="os_dt_fim"
    )

    # Validation
    if dt_ini > dt_fim:
        st.sidebar.error("⚠️ Data início deve ser anterior à data fim")
        # Reset to valid values
        dt_ini = state.get("dt_ini", date.today().replace(day=1))
        dt_fim = state.get("dt_fim", date.today())

    # Estado filter
    st.sidebar.markdown("#### 📍 Estados")
    if estados:
        est_map = {e["descricao"]: e["id"] for e in estados}
        est_desc = st.sidebar.multiselect(
            "Selecione os estados",
            list(est_map.keys()),
            default=[k for k, v in est_map.items() if v in state.get("estado_ids", [])],
            key="os_estados",
            help="Deixe vazio para incluir todos os estados"
        )
        estado_ids = [est_map[d] for d in est_desc]
    else:
        estado_ids = []
        st.sidebar.warning("Não foi possível carregar estados")

    # Action buttons
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)

    apply_clicked = col1.button("✅ Aplicar", key="os_apply")
    clear_clicked = col2.button("🗑️ Limpar", key="os_clear")

    # Handle button actions
    if apply_clicked:
        st.session_state["os_filters"] = {
            "dt_ini": dt_ini,
            "dt_fim": dt_fim,
            "estado_ids": estado_ids,
        }
        st.session_state["os_filters_version"] += 1
        st.sidebar.success("✅ Filtros aplicados!")
        st.rerun()

    elif clear_clicked:
        st.session_state["os_filters"] = {
            "dt_ini": date.today().replace(day=1),
            "dt_fim": date.today(),
            "estado_ids": [],
        }
        st.session_state["os_filters_version"] += 1
        st.sidebar.success("🗑️ Filtros limpos!")
        st.rerun()

    return st.session_state.get("os_filters", {})


def show_os_active_filters(client: ArkmedsClient) -> None:
    """Exibe os filtros ativos de Ordem de Serviço."""
    filters = st.session_state.get("os_filters")
    if not filters:
        return

    # Build filter display
    parts = []

    # Date range
    dt_ini = filters.get("dt_ini")
    dt_fim = filters.get("dt_fim")
    if dt_ini and dt_fim:
        if dt_ini == dt_fim:
            parts.append(f"📅 {dt_ini.strftime('%d/%m/%Y')}")
        else:
            parts.append(f"📅 {dt_ini.strftime('%d/%m/%Y')} – {dt_fim.strftime('%d/%m/%Y')}")

    # Estados
    estado_ids = filters.get("estado_ids", [])
    if estado_ids:
        try:
            estados = _get_estados_os(client)
            estado_names = [e["descricao"] for e in estados if e["id"] in estado_ids]
            if estado_names:
                if len(estado_names) <= 3:
                    parts.append(f"📍 {', '.join(estado_names)}")
                else:
                    parts.append(f"📍 {len(estado_names)} estados selecionados")
        except Exception:
            pass
    else:
        parts.append("📍 Todos os estados")

    if parts:
        st.info(f"**Filtros ativos:** {' • '.join(parts)}")
