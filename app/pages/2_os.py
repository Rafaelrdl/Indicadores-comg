import asyncio

import pandas as pd
import streamlit as st

from app.arkmeds_client.client import ArkmedsClient
from app.services.os_metrics import compute_metrics
from app.ui.filters import show_active_filters

st.set_page_config(page_title="Ordens de Serviço", page_icon="📑")

filters = st.session_state["filters"]
version = st.session_state.get("filtros_version", 0)

@st.cache_data(ttl=900, experimental_allow_widgets=True)
async def get_data(v: int):
    client = ArkmedsClient.from_session()
    metrics = await compute_metrics(client, **filters)
    dt_ini = filters.get("dt_ini")
    dt_fim = filters.get("dt_fim")
    extra = {k: v for k, v in filters.items() if k not in {"dt_ini", "dt_fim"}}
    os_raw = await client.list_os(
        data_criacao__gte=dt_ini,
        data_criacao__lte=dt_fim,
        **extra,
    )
    return metrics, os_raw

with st.spinner("Calculando KPIs…"):
    metrics, os_raw = asyncio.run(get_data(version))

show_active_filters(ArkmedsClient.from_session())

cols = st.columns(3)
cols[0].metric("🛠️ Corretiva Predial", metrics.corretivas_predial)
cols[1].metric("⚙️ Corretiva Eng.Cli.", metrics.corretivas_engenharia)
cols[2].metric("🔧 Preventiva Predial", metrics.preventivas_predial)
cols = st.columns(3)
cols[0].metric("🛠️ Preventiva Infra", metrics.preventivas_infra)
cols[1].metric("🔍 Busca Ativa", metrics.busca_ativa)
cols[2].metric("📦 Backlog", metrics.backlog)
cols = st.columns(3)
cols[0].metric("⏱️ SLA %", metrics.sla_pct)

abertas_total = metrics.backlog
fechadas_total = (
    metrics.corretivas_predial
    + metrics.corretivas_engenharia
    + metrics.preventivas_predial
    + metrics.preventivas_infra
    + metrics.busca_ativa
    - metrics.backlog
)
st.bar_chart({"Abertas": [abertas_total], "Fechadas": [fechadas_total]})

df = pd.DataFrame([o.model_dump() for o in os_raw])
st.dataframe(df, use_container_width=True)

st.download_button(
    "⬇️ Baixar CSV",
    df.to_csv(index=False).encode(),
    "ordens_servico.csv",
)
