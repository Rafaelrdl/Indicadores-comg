import asyncio

import pandas as pd
import streamlit as st
from arkmeds_client.client import ArkmedsClient
from services.os_metrics import compute_metrics

from ui.filters import show_active_filters

st.set_page_config(page_title="Ordens de Serviço", page_icon="📑", layout="wide")

filters = st.session_state["filters"]
version = st.session_state.get("filtros_version", 0)

@st.cache_data(ttl=900)
def get_data(v: int):
    """Wrapper síncrono para executar e cachear os resultados da função assíncrona."""

    async def _get_data_async():
        """Função assíncrona que busca os dados."""
        client = ArkmedsClient.from_session()
        
        # Extrair datas e outros filtros
        dt_ini = filters.get("dt_ini")
        dt_fim = filters.get("dt_fim")
        extra = {k: v for k, v in filters.items() if k not in {"dt_ini", "dt_fim"}}
        
        # Chamar compute_metrics com os parâmetros corretos
        metrics_task = compute_metrics(client, start_date=dt_ini, end_date=dt_fim, **extra)
        
        os_raw_task = client.list_os(
            data_criacao__gte=dt_ini,
            data_criacao__lte=dt_fim,
            **extra,
        )
        metrics, os_raw = await asyncio.gather(metrics_task, os_raw_task)
        return metrics, os_raw

    return asyncio.run(_get_data_async())


with st.spinner("Calculando KPIs…"):
    metrics, os_raw = get_data(version)

show_active_filters(ArkmedsClient.from_session())

cols = st.columns(3)
cols[0].metric("🛠️ Corretiva Predial", metrics.corrective_building)
cols[1].metric("⚙️ Corretiva Eng.Cli.", metrics.corrective_engineering)
cols[2].metric("🔧 Preventiva Predial", metrics.preventive_building)
cols = st.columns(3)
cols[0].metric("🛠️ Preventiva Infra", metrics.preventive_infra)
cols[1].metric("🔍 Busca Ativa", metrics.active_search)
cols[2].metric("📦 Backlog", metrics.backlog)
cols = st.columns(3)
cols[0].metric("⏱️ SLA %", metrics.sla_percentage)

abertas_total = metrics.backlog
fechadas_total = (
    metrics.corrective_building
    + metrics.corrective_engineering
    + metrics.preventive_building
    + metrics.preventive_infra
    + metrics.active_search
)
st.bar_chart({"Abertas": [abertas_total], "Fechadas": [fechadas_total]})

df = pd.DataFrame([o.model_dump() for o in os_raw])
st.dataframe(df, use_container_width=True)

st.download_button(
    "⬇️ Baixar CSV",
    df.to_csv(index=False).encode(),
    "ordens_servico.csv",
)
