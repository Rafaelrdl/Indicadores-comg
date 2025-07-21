import streamlit as st
from datetime import date, timedelta
from src.arkmeds_api import (
    ID_OS_CORRETIVA,
    ID_ESTADO_FECHADA,
    list_tipos,
    list_estados,
    list_responsaveis,
    get_os_count,
)

st.set_page_config(page_title="OS Metrics", layout="wide")

# ----- Sidebar -----
st.sidebar.header("Filtros")

# Período – default mês atual
hoje = date.today()
primeiro_dia = hoje.replace(day=1)
ultimo_dia = (primeiro_dia + timedelta(days=32)).replace(day=1) - timedelta(days=1)

dt_ini = st.sidebar.date_input("Início", value=primeiro_dia)
dt_fim = st.sidebar.date_input("Fim", value=ultimo_dia)

tipos = list_tipos()
tipos_opts = {t["label"]: t["id"] for t in tipos}
tipo_sel = st.sidebar.selectbox(
    "Tipo de OS", options=["(Todas)"] + list(tipos_opts.keys()), index=0
)

estados = list_estados()
estados_opts = {e["label"]: e["id"] for e in estados}
estados_sel = st.sidebar.multiselect("Estado da OS", options=list(estados_opts.keys()))

resp = list_responsaveis()
resp_opts = {r["label"]: r["id"] for r in resp}
resp_sel = st.sidebar.selectbox(
    "Responsável Técnico", options=["(Todos)"] + list(resp_opts.keys()), index=0
)

# ----- Construção dos filtros -----
tipo_id = tipos_opts.get(tipo_sel) if tipo_sel != "(Todas)" else None
estado_ids = [estados_opts[e] for e in estados_sel] if estados_sel else None
resp_id = resp_opts.get(resp_sel) if resp_sel != "(Todos)" else None

# ----- Métricas principais -----
with st.spinner("Consultando Arkmeds..."):
    # Métrica 1 – abertas (respeitando filtros; se nenhum filtro, corrige para corretivas)
    abertas = get_os_count(
        dt_ini=dt_ini,
        dt_fim=dt_fim,
        tipo_id=tipo_id or ID_OS_CORRETIVA,
        responsavel_id=resp_id,
        estado_ids=estado_ids,  # None -> todos
    )

    # Métrica 2 – fechadas (estado Fechada + demais filtros)
    fechadas = get_os_count(
        dt_ini=dt_ini,
        dt_fim=dt_fim,
        tipo_id=tipo_id or ID_OS_CORRETIVA,
        responsavel_id=resp_id,
        estado_ids=estado_ids or [ID_ESTADO_FECHADA],
    )

col1, col2 = st.columns(2)
col1.metric("OS Abertas", abertas)
col2.metric("OS Fechadas", fechadas)

st.bar_chart({"Abertas": [abertas], "Fechadas": [fechadas]})

# Info dos filtros ativos
filtros = []
if tipo_id:
    filtros.append(f"Tipo: {tipo_sel}")
if estados_sel:
    filtros.append(f"Estados: {', '.join(estados_sel)}")
if resp_id:
    filtros.append(f"Resp. Técnico: {resp_sel}")
st.caption(
    "Filtros ativos: "
    + ("; ".join(filtros) if filtros else "Nenhum (padrão ‘corretivas’)")
)
