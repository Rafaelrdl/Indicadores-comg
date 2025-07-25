import asyncio
from collections import defaultdict
from datetime import date
from statistics import mean

import pandas as pd
import plotly.express as px
import streamlit as st
from arkmeds_client.client import ArkmedsClient
from arkmeds_client.models import Chamado
from config.os_types import TIPO_CORRETIVA
from dateutil.relativedelta import relativedelta
from services.equip_metrics import compute_metrics
from services.equip_advanced_metrics import (
    calcular_stats_equipamentos,
    calcular_mttf_mtbf_top,
    exibir_distribuicao_prioridade,
    exibir_distribuicao_status,
    exibir_top_mttf_mtbf,
)
from app.ui.utils import run_async_safe

st.set_page_config(page_title="Equipamentos", page_icon="🛠️", layout="wide")

# Nota: Equipamentos não usam filtros de data/tipo/estado pois são dados estáticos
# version = st.session_state.get("filtros_version", 0)  # Não usado mais
version = 1  # Versão fixa para equipamentos


def _build_history_df(os_list: list[Chamado]) -> pd.DataFrame:
    mttr_map: dict[date, list[float]] = defaultdict(list)
    by_eq: dict[int | None, list[Chamado]] = defaultdict(list)
    for os_obj in os_list:
        # Para Chamado, precisamos extrair dados da ordem_servico
        data_fechamento_str = os_obj.ordem_servico.get("data_fechamento") if os_obj.ordem_servico else None
        if not data_fechamento_str:
            continue
        
        # Parse das datas
        try:
            from datetime import datetime
            data_criacao = datetime.strptime(os_obj.data_criacao_os, "%d/%m/%y - %H:%M")
            data_fechamento = datetime.strptime(data_fechamento_str, "%d/%m/%y - %H:%M")
        except (ValueError, TypeError):
            continue
            
        month = data_fechamento.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        delta_h = (data_fechamento - data_criacao).total_seconds() / 3600
        mttr_map[month].append(delta_h)
        by_eq[os_obj.equipamento_id].append(os_obj)

    mtbf_map: dict[date, list[float]] = defaultdict(list)
    for items in by_eq.values():
        if len(items) < 2:
            continue
        items.sort(key=lambda o: datetime.strptime(o.data_criacao_os, "%d/%m/%y - %H:%M"))
        for i in range(1, len(items)):
            current_date = datetime.strptime(items[i].data_criacao_os, "%d/%m/%y - %H:%M")
            previous_date = datetime.strptime(items[i-1].data_criacao_os, "%d/%m/%y - %H:%M")
            month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
            interval_h = (current_date - previous_date).total_seconds() / 3600
            mtbf_map[month].append(interval_h)

    months = sorted(set(mttr_map.keys()) | set(mtbf_map.keys()))
    data = {
        "mes": months,
        "mttr": [round(mean(mttr_map[m]), 2) if mttr_map.get(m) else 0 for m in months],
        "mtbf": [round(mean(mtbf_map[m]), 2) if mtbf_map.get(m) else 0 for m in months],
    }
    return pd.DataFrame(data)


@st.cache_data(ttl=900)
def fetch_data(v: int):
    """Wrapper síncrono para executar e cachear os resultados da função assíncrona."""
    
    async def _fetch_data_async():
        """Função assíncrona que busca os dados."""
        client = ArkmedsClient.from_session()
        
        # Para equipamentos, usaremos período fixo dos últimos 12 meses
        from dateutil.relativedelta import relativedelta
        dt_fim = date.today()
        dt_ini = dt_fim - relativedelta(months=12)
        
        # Sem filtros extras pois equipamentos não dependem de tipo/estado/responsável
        metrics_task = compute_metrics(client, start_date=dt_ini, end_date=dt_fim)
        
        equip_task = client.list_equipamentos()
        
        hist_ini = date.today().replace(day=1) - relativedelta(months=11)
        os_hist_task = client.list_os(
            tipo_id=TIPO_CORRETIVA,
            data_fechamento__gte=hist_ini,
            data_fechamento__lte=date.today(),
        )
        
        metrics, equip, os_hist = await asyncio.gather(metrics_task, equip_task, os_hist_task)
        return metrics, equip, os_hist
    
    return run_async_safe(_fetch_data_async())


# Função para buscar estatísticas avançadas
@st.cache_data(ttl=900)
def fetch_advanced_stats(v: int):
    """Busca estatísticas avançadas dos equipamentos."""
    client = ArkmedsClient.from_session()
    return calcular_stats_equipamentos(client)


# Função para buscar dados de MTTF/MTBF
@st.cache_data(ttl=1800)  # Cache mais longo pois é pesado
def fetch_mttf_mtbf_data(v: int):
    """Busca dados de MTTF/MTBF."""
    client = ArkmedsClient.from_session()
    return calcular_mttf_mtbf_top(client)


with st.spinner("Carregando dados de equipamentos…"):
    metrics, equip_list, os_hist = fetch_data(version)

# Nota: Filtros removidos pois não se aplicam a equipamentos
# show_active_filters(ArkmedsClient.from_session())

# Seção 1: Métricas básicas
st.header("📊 Métricas Básicas de Equipamentos")

pct_em_manut = round(metrics.em_manutencao / metrics.ativos * 100, 1) if metrics.ativos else 0
idades = [
    (date.today() - eq.data_aquisicao.date()).days / 365
    for eq in equip_list
    if eq.data_aquisicao
]
idade_media = round(mean(idades), 1) if idades else 0

cols = st.columns(4)
cols[0].metric("🔋 Ativos", metrics.ativos)
cols[1].metric("🚫 Desativados", metrics.desativados)
cols[2].metric("🔧 Em manutenção", metrics.em_manutencao)
cols[3].metric("⏱️ MTTR (h)", metrics.mttr_h)
cols = st.columns(3)
cols[0].metric("🔄 MTBF (h)", metrics.mtbf_h)
cols[1].metric("⚠️ % Ativos EM", pct_em_manut)
cols[2].metric("📅 Idade média", idade_media)

# Seção 2: Estatísticas Avançadas
st.header("📈 Análise Avançada de Equipamentos")

with st.spinner("Carregando estatísticas avançadas..."):
    advanced_stats = fetch_advanced_stats(version)

# Sub-seção: Status dos equipamentos
st.subheader("🔋 Status dos Equipamentos")
exibir_distribuicao_status(advanced_stats)

# Sub-seção: Distribuição de prioridade
st.subheader("🎯 Distribuição de Prioridade")
exibir_distribuicao_prioridade(advanced_stats)

# Seção 3: Histórico MTTR vs MTBF
st.header("📉 Histórico de Manutenção (Últimos 12 meses)")

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

# Seção 4: Top Rankings MTTF/MTBF
st.header("🏆 Top Rankings de Confiabilidade")

# Aviso sobre processamento
with st.expander("ℹ️ Sobre os cálculos de MTTF/MTBF"):
    st.info("""
    **MTTF (Mean Time To Failure)**: Tempo médio até a primeira falha após aquisição.
    Equipamentos com maior MTTF são mais confiáveis.
    
    **MTBF (Mean Time Between Failures)**: Tempo médio entre falhas consecutivas.
    Equipamentos com maior MTBF têm maior disponibilidade.
    
    ⚠️ **Nota**: Este cálculo pode demorar alguns minutos pois analisa o histórico completo
    de manutenções de todos os equipamentos.
    """)

# Checkbox para habilitar cálculo pesado
calcular_rankings = st.checkbox(
    "🔄 Calcular Rankings MTTF/MTBF",
    help="Este cálculo pode demorar alguns minutos. Deixe marcado apenas se necessário."
)

if calcular_rankings:
    with st.spinner("Calculando rankings MTTF/MTBF... Isso pode demorar alguns minutos..."):
        try:
            top_mttf, top_mtbf = fetch_mttf_mtbf_data(version)
            exibir_top_mttf_mtbf(top_mttf, top_mtbf)
        except Exception as e:
            st.error(f"Erro ao calcular rankings: {e}")
            st.info("Tente novamente em alguns minutos.")

# Seção 5: Tabela detalhada (mantida igual)
st.header("📋 Lista Detalhada de Equipamentos")


def _table_data() -> pd.DataFrame:
    df = pd.DataFrame([e.model_dump() for e in equip_list])
    df["status"] = df["ativo"].map({True: "Ativo", False: "Desativado"})
    df["idade_anos"] = df["data_aquisicao"].apply(
        lambda d: round((date.today() - d.date()).days / 365, 1) if d else None
    )
    by_eq: dict[int, list[Chamado]] = defaultdict(list)
    for os_obj in os_hist:
        # Verificar se o chamado tem data de fechamento e equipamento
        data_fechamento_str = os_obj.ordem_servico.get("data_fechamento") if os_obj.ordem_servico else None
        if os_obj.equipamento_id is not None and data_fechamento_str:
            by_eq[os_obj.equipamento_id].append(os_obj)
    
    mttr_local = []
    mtbf_local = []
    ultima_os = []
    
    for eq in df["id"]:
        items = by_eq.get(eq, [])
        if items:
            # Calcular datas de fechamento para obter a última OS
            datas_fechamento = []
            for o in items:
                data_fechamento_str = o.ordem_servico.get("data_fechamento")
                if data_fechamento_str:
                    try:
                        data_fechamento = datetime.strptime(data_fechamento_str, "%d/%m/%y - %H:%M")
                        datas_fechamento.append(data_fechamento)
                    except (ValueError, TypeError):
                        continue
            
            if datas_fechamento:
                ultima_os.append(max(datas_fechamento).date())
                
                # Calcular MTTR
                tempos_reparo = []
                for o in items:
                    try:
                        data_criacao = datetime.strptime(o.data_criacao_os, "%d/%m/%y - %H:%M")
                        data_fechamento_str = o.ordem_servico.get("data_fechamento")
                        if data_fechamento_str:
                            data_fechamento = datetime.strptime(data_fechamento_str, "%d/%m/%y - %H:%M")
                            tempo_reparo = (data_fechamento - data_criacao).total_seconds()
                            tempos_reparo.append(tempo_reparo)
                    except (ValueError, TypeError):
                        continue
                
                mttr_local.append(
                    round(mean(tempos_reparo) / 3600, 2) if tempos_reparo else 0.0
                )
                
                # Calcular MTBF
                if len(items) > 1:
                    items.sort(key=lambda o: datetime.strptime(o.data_criacao_os, "%d/%m/%y - %H:%M"))
                    intervals = []
                    for i in range(1, len(items)):
                        try:
                            data_atual = datetime.strptime(items[i].data_criacao_os, "%d/%m/%y - %H:%M")
                            data_anterior = datetime.strptime(items[i-1].data_criacao_os, "%d/%m/%y - %H:%M")
                            interval = (data_atual - data_anterior).total_seconds()
                            intervals.append(interval)
                        except (ValueError, TypeError):
                            continue
                    mtbf_local.append(round(mean(intervals) / 3600, 2) if intervals else 0.0)
                else:
                    mtbf_local.append(0.0)
            else:
                ultima_os.append(None)
                mttr_local.append(0.0)
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
