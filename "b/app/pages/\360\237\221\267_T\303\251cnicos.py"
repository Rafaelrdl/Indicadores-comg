import asyncio
import statistics

import pandas as pd
import plotly.express as px
import streamlit as st

from app.arkmeds_client.client import ArkmedsClient
from app.services.tech_metrics import compute_metrics

from .filters import show_active_filters

filters = st.session_state["filters"]
version = st.session_state.get("filtros_version", 0)


@st.cache_data(ttl=900, experimental_allow_widgets=True)
async def fetch_data(v: int):
    client = ArkmedsClient.from_session()
    tech_kpi = await compute_metrics(client, **filters)
    return tech_kpi

with st.spinner("Calculando KPIs dos técnicos…"):
    kpis = asyncio.run(fetch_data(version))

show_active_filters(ArkmedsClient.from_session())

total_tecnicos = len(kpis)
pendentes_totais = sum(t.pendentes_total for t in kpis)
sla_medio = round(statistics.mean(t.sla_pct for t in kpis), 1) if kpis else 0

cols = st.columns(3)
cols[0].metric("👷 Técnicos", total_tecnicos)
cols[1].metric("📦 OS Pendentes", pendentes_totais)
cols[2].metric("⏱️ SLA médio (%)", sla_medio)

df = pd.DataFrame([t.model_dump() for t in kpis])
df = df.rename(
    columns={
        "abertas": "Abertas (período)",
        "concluidas": "Concluídas",
        "pendentes_total": "Pendentes",
        "sla_pct": "SLA %",
        "avg_close_h": "Média (h)",
    }
)

st.dataframe(df.sort_values("Pendentes", ascending=False), use_container_width=True)

st.download_button("⬇️ CSV", df.to_csv(index=False).encode(), "tecnicos.csv")

df_top = df.nlargest(10, "Pendentes")
fig = px.bar(
    df_top,
    y="nome",
    x=["Pendentes", "Concluídas"],
    orientation="h",
    barmode="stack",
    labels={"value": "OS", "nome": "Técnico"},
)
st.plotly_chart(fig, use_container_width=True)
