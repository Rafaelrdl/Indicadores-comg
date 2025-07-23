import asyncio
from collections import defaultdict
from datetime import date
from statistics import mean

import pandas as pd
import plotly.express as px
import streamlit as st
from dateutil.relativedelta import relativedelta

from app.arkmeds_client.client import ArkmedsClient
from app.arkmeds_client.models import OS
from app.config.os_types import TIPO_CORRETIVA
from app.services.equip_metrics import compute_metrics

from .filters import show_active_filters

filters = st.session_state["filters"]
version = st.session_state.get("filtros_version", 0)


def _build_history_df(os_list: list[OS]) -> pd.DataFrame:
    mttr_map: dict[date, list[float]] = defaultdict(list)
    by_eq: dict[int | None, list[OS]] = defaultdict(list)
    for os_obj in os_list:
        if os_obj.closed_at is None:
            continue
        month = os_obj.closed_at.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        delta_h = (os_obj.closed_at - os_obj.created_at).total_seconds() / 3600
        mttr_map[month].append(delta_h)
        by_eq[os_obj.equipment_id].append(os_obj)

    mtbf_map: dict[date, list[float]] = defaultdict(list)
    for items in by_eq.values():
        if len(items) < 2:
            continue
        items.sort(key=lambda o: o.created_at)
        for i in range(1, len(items)):
            month = items[i].created_at.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
            interval_h = (items[i].created_at - items[i - 1].created_at).total_seconds() / 3600
            mtbf_map[month].append(interval_h)

    months = sorted(set(mttr_map.keys()) | set(mtbf_map.keys()))
    data = {
        "mes": months,
        "mttr": [round(mean(mttr_map[m]), 2) if mttr_map.get(m) else 0 for m in months],
        "mtbf": [round(mean(mtbf_map[m]), 2) if mtbf_map.get(m) else 0 for m in months],
    }
    return pd.DataFrame(data)


@st.cache_data(ttl=900, experimental_allow_widgets=True)
async def fetch_data(v: int):
    client = ArkmedsClient.from_session()
    metrics = await compute_metrics(client, **filters)
    equip = await client.list_equipment()
    hist_ini = date.today().replace(day=1) - relativedelta(months=11)
    os_hist = await client.list_os(
        tipo_id=TIPO_CORRETIVA,
        data_fechamento__gte=hist_ini,
        data_fechamento__lte=date.today(),
    )
    return metrics, equip, os_hist


with st.spinner("Carregando dados de equipamentos…"):
    metrics, equip_list, os_hist = asyncio.run(fetch_data(version))

show_active_filters(ArkmedsClient.from_session())

pct_em_manut = round(metrics.em_manutencao / metrics.ativos * 100, 1) if metrics.ativos else 0
idade_media = round(
    mean(
        [
            (date.today() - eq.data_aquisicao.date()).days / 365
            for eq in equip_list
            if eq.data_aquisicao
        ]
    ),
    1,
) if equip_list else 0

cols = st.columns(4)
cols[0].metric("🔋 Ativos", metrics.ativos)
cols[1].metric("🚫 Desativados", metrics.desativados)
cols[2].metric("🔧 Em manutenção", metrics.em_manutencao)
cols[3].metric("⏱️ MTTR (h)", metrics.mttr_h)
cols = st.columns(3)
cols[0].metric("🔄 MTBF (h)", metrics.mtbf_h)
cols[1].metric("⚠️ % Ativos EM", pct_em_manut)
cols[2].metric("📅 Idade média", idade_media)

hist_df = _build_history_df(os_hist)
if len(hist_df) >= 1:
    fig = px.line(
        hist_df,
        x="mes",
        y=["mttr", "mtbf"],
        markers=True,
        labels={"value": "Horas", "variable": ""},
        title="MTTR vs MTBF (últimos 12 meses)",
    )
    st.plotly_chart(fig, use_container_width=True)


def _table_data() -> pd.DataFrame:
    df = pd.DataFrame([e.model_dump() for e in equip_list])
    df["status"] = df["ativo"].map({True: "Ativo", False: "Desativado"})
    df["idade_anos"] = df["data_aquisicao"].apply(
        lambda d: round((date.today() - d.date()).days / 365, 1) if d else None
    )
    by_eq: dict[int, list[OS]] = defaultdict(list)
    for os_obj in os_hist:
        if os_obj.equipment_id is not None and os_obj.closed_at:
            by_eq[os_obj.equipment_id].append(os_obj)
    mttr_local = []
    mtbf_local = []
    ultima_os = []
    for eq in df["id"]:
        items = by_eq.get(eq, [])
        if items:
            ultima_os.append(max(o.closed_at for o in items).date())
            mttr_local.append(
                round(
                    mean(
                        (
                            (o.closed_at - o.created_at).total_seconds()
                            for o in items
                        )
                    )
                    / 3600,
                    2,
                )
            )
            if len(items) > 1:
                items.sort(key=lambda o: o.created_at)
                intervals = [
                    (
                        items[i].created_at - items[i - 1].created_at
                    ).total_seconds()
                    for i in range(1, len(items))
                ]
                mtbf_local.append(round(mean(intervals) / 3600, 2))
            else:
                mtbf_local.append(0.0)
        else:
            ultima_os.append(None)
            mttr_local.append(0.0)
            mtbf_local.append(0.0)
    df["ultima_os"] = ultima_os
    df["mttr_local"] = mttr_local
    df["mtbf_local"] = mtbf_local
    return df


df = _table_data()
st.dataframe(df, height=500, use_container_width=True)

st.download_button("⬇️ Baixar CSV", df.to_csv(index=False).encode(), "equipamentos.csv")
