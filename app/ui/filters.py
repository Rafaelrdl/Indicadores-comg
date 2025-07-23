from __future__ import annotations

import asyncio
import time
from datetime import date
from typing import List

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from app.arkmeds_client.client import ArkmedsClient
from app.arkmeds_client.models import EstadoOS, TipoOS, User

_FAKE_SESSION: dict = {}


def _session() -> dict:
    """Return Streamlit session state or a fallback dict when offline."""
    ctx = get_script_run_ctx()
    if ctx is None:
        # not running via `streamlit run`, fallback to local dict
        global _FAKE_SESSION
        # replace Streamlit proxy with plain dict for test assertions
        st.session_state = _FAKE_SESSION
        return _FAKE_SESSION
    return st.session_state

@st.cache_data(ttl=86400)
def _get_tipos(_client: ArkmedsClient) -> List[TipoOS]:
    return asyncio.run(_client.list_tipos())


@st.cache_data(ttl=86400)
def _get_estados(_client: ArkmedsClient) -> List[EstadoOS]:
    return asyncio.run(_client.list_estados())


@st.cache_data(ttl=86400)
def _get_users(_client: ArkmedsClient) -> List[User]:
    return asyncio.run(_client.list_users(perfil="responsavel_tecnico"))


def render_filters(client: ArkmedsClient) -> dict:
    sess = _session()
    state = sess.get("filters", {})
    sess.setdefault("filtros_version", 0)

    start = time.time()
    tipos = _get_tipos(client)
    estados = _get_estados(client)
    users = _get_users(client)
    if time.time() - start > 1:
        st.warning("Carregando opções…")

    dt_ini = st.sidebar.date_input("Data início", value=state.get("dt_ini"))
    dt_fim = st.sidebar.date_input("Data fim", value=state.get("dt_fim"))
    if dt_ini > dt_fim:
        st.sidebar.error("Data início deve ser anterior à data fim")

    tipo_map = {"(Todos)": None, **{t.descricao: t.id for t in tipos}}
    tipo_desc = st.sidebar.selectbox(
        "🏷️ Tipo de OS",
        list(tipo_map.keys()),
        index=list(tipo_map.values()).index(state.get("tipo_id")) if state.get("tipo_id") in tipo_map.values() else 0,
    )
    tipo_id = tipo_map[tipo_desc]

    est_map = {e.descricao: e.id for e in estados}
    est_desc = st.sidebar.multiselect(
        "📍 Estado",
        list(est_map.keys()),
        default=[k for k, v in est_map.items() if v in state.get("estado_ids", [])],
    )
    estado_ids = [est_map[d] for d in est_desc]

    user_map = {"(Todos)": None, **{u.nome: u.id for u in users}}
    user_desc = st.sidebar.selectbox(
        "👤 Responsável",
        list(user_map.keys()),
        index=list(user_map.values()).index(state.get("responsavel_id")) if state.get("responsavel_id") in user_map.values() else 0,
    )
    responsavel_id = user_map[user_desc]

    apply_clicked = st.sidebar.button("Aplicar")
    clear_clicked = st.sidebar.button("Limpar")

    if apply_clicked:
        sess["filters"] = {
            "dt_ini": dt_ini,
            "dt_fim": dt_fim,
            "tipo_id": tipo_id,
            "estado_ids": estado_ids,
            "responsavel_id": responsavel_id,
        }
        sess["filtros_version"] += 1
    elif clear_clicked:
        sess["filters"] = {
            "dt_ini": date.today().replace(day=1),
            "dt_fim": date.today(),
            "tipo_id": None,
            "estado_ids": [],
            "responsavel_id": None,
        }
        sess["filtros_version"] += 1

    return sess.get("filters", {})


def show_active_filters(client: ArkmedsClient) -> None:
    sess = _session()
    filters = sess.get("filters")
    if not filters:
        return
    parts = [
        f"🗓️ {filters['dt_ini']:%d/%m} – {filters['dt_fim']:%d/%m}"
    ]
    if filters.get("tipo_id"):
        tipos = _get_tipos(client)
        desc = next((t.descricao for t in tipos if t.id == filters["tipo_id"]), None)
        if desc:
            parts.append(desc)
    if filters.get("responsavel_id"):
        users = _get_users(client)
        desc = next((u.nome for u in users if u.id == filters["responsavel_id"]), None)
        if desc:
            parts.append(desc)
    st.write(" • ".join(parts))
