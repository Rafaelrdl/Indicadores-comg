"""Página de análise de ordens de serviço e KPIs de manutenção."""

import asyncio
from typing import Tuple

import pandas as pd
import streamlit as st

from arkmeds_client.client import ArkmedsClient
from services.os_metrics import compute_metrics
from app.ui.utils import run_async_safe
from app.ui.filters import show_active_filters
from app.core.logging import performance_monitor, log_cache_performance, app_logger
from app.core.exceptions import ErrorHandler, DataFetchError, safe_operation

# Configuração da página
st.set_page_config(
    page_title="Ordens de Serviço", 
    page_icon="📑", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constantes
CACHE_TTL_DEFAULT = 900  # 15 minutos

@st.cache_data(ttl=CACHE_TTL_DEFAULT, show_spinner="Carregando dados de ordens de serviço...")
@log_cache_performance
@performance_monitor
def fetch_os_data() -> Tuple:
    """Busca dados de ordens de serviço e métricas."""
    
    @safe_operation(
        fallback_value=(None, []),
        error_message="Erro ao buscar dados de ordens de serviço"
    )
    def _safe_fetch():
        async def _fetch_data_async():
            client = ArkmedsClient.from_session()
            filters = st.session_state["filters"]
            
            # Extrair datas e outros filtros
            dt_ini = filters.get("dt_ini")
            dt_fim = filters.get("dt_fim")
            extra = {k: v for k, v in filters.items() if k not in {"dt_ini", "dt_fim"}}
            
            # Buscar métricas e OS em paralelo
            metrics_task = compute_metrics(client, start_date=dt_ini, end_date=dt_fim, **extra)
            os_raw_task = client.list_os(
                data_criacao__gte=dt_ini,
                data_criacao__lte=dt_fim,
                **extra,
            )
            
            return await asyncio.gather(metrics_task, os_raw_task)
        
        return run_async_safe(_fetch_data_async())
    
    return _safe_fetch()


def render_kpi_metrics(metrics) -> None:
    """Renderiza as métricas principais de KPI."""
    st.header("📊 KPIs de Manutenção")
    
    # Primeira linha de métricas
    cols = st.columns(3)
    cols[0].metric("🛠️ Corretiva Predial", metrics.corrective_building)
    cols[1].metric("⚙️ Corretiva Eng.Cli.", metrics.corrective_engineering)
    cols[2].metric("🔧 Preventiva Predial", metrics.preventive_building)
    
    # Segunda linha de métricas
    cols = st.columns(3)
    cols[0].metric("🛠️ Preventiva Infra", metrics.preventive_infra)
    cols[1].metric("🔍 Busca Ativa", metrics.active_search)
    cols[2].metric("📦 Backlog", metrics.backlog)
    
    # Terceira linha com SLA
    cols = st.columns(3)
    cols[0].metric("⏱️ SLA %", f"{metrics.sla_percentage:.1f}%")


def render_summary_chart(metrics) -> None:
    """Renderiza gráfico resumo de abertas vs fechadas."""
    st.header("📈 Resumo Geral")
    
    abertas_total = metrics.backlog
    fechadas_total = (
        metrics.corrective_building
        + metrics.corrective_engineering
        + metrics.preventive_building
        + metrics.preventive_infra
        + metrics.active_search
    )
    
    # Criar DataFrame para o gráfico
    chart_data = pd.DataFrame({
        "Status": ["Abertas", "Fechadas"],
        "Quantidade": [abertas_total, fechadas_total]
    })
    
    st.bar_chart(chart_data.set_index("Status"))
    
    # Mostrar percentuais
    total = abertas_total + fechadas_total
    if total > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📈 Taxa de Resolução", f"{(fechadas_total/total)*100:.1f}%")
        with col2:
            st.metric("📊 Total de OS", total)


def render_os_table(os_raw: list) -> None:
    """Renderiza tabela detalhada de ordens de serviço."""
    st.header("📋 Lista de Ordens de Serviço")
    
    if not os_raw:
        st.info("Nenhuma ordem de serviço encontrada para os filtros selecionados.")
        return
    
    # Converter para DataFrame
    df = pd.DataFrame([o.model_dump() for o in os_raw])
    
    # Filtros da tabela
    col1, col2 = st.columns(2)
    with col1:
        if 'tipo' in df.columns:
            tipos_disponiveis = ["Todos"] + sorted(df['tipo'].dropna().unique().tolist())
            tipo_filter = st.selectbox("Filtrar por Tipo:", tipos_disponiveis, index=0)
    
    with col2:
        if 'status' in df.columns:
            status_disponiveis = ["Todos"] + sorted(df['status'].dropna().unique().tolist())
            status_filter = st.selectbox("Filtrar por Status:", status_disponiveis, index=0)
    
    # Aplicar filtros
    filtered_df = df.copy()
    if 'tipo' in df.columns and tipo_filter != "Todos":
        filtered_df = filtered_df[filtered_df['tipo'] == tipo_filter]
    if 'status' in df.columns and status_filter != "Todos":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    # Exibir tabela
    st.dataframe(
        filtered_df, 
        use_container_width=True,
        height=400
    )
    
    # Botão de download
    st.download_button(
        "⬇️ Baixar CSV",
        filtered_df.to_csv(index=False).encode(),
        "ordens_servico.csv",
        mime="text/csv"
    )
    
    # Estatísticas da tabela
    if len(filtered_df) > 0:
        st.info(f"📊 Exibindo {len(filtered_df)} de {len(df)} ordens de serviço")


def main():
    """Função principal da página de ordens de serviço."""
    st.title("📑 Ordens de Serviço")
    
    # Buscar dados
    metrics, os_raw = fetch_os_data()
    
    # Mostrar filtros ativos
    show_active_filters(ArkmedsClient.from_session())
    
    # Renderizar seções
    render_kpi_metrics(metrics)
    st.divider()
    
    render_summary_chart(metrics)
    st.divider()
    
    render_os_table(os_raw)


# Executar a aplicação
main()
