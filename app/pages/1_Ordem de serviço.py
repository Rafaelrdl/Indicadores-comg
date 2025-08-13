"""Página de análise de ordens de serviço e KPIs de manutenção."""

import asyncio
from typing import Tuple

import pandas as pd
import streamlit as st

from arkmeds_client.client import ArkmedsClient
from services.os_metrics import compute_metrics
from app.ui.utils import run_async_safe
from app.ui.os_filters import render_os_filters, show_os_active_filters

# New infrastructure imports
from app.core import get_settings, APIError, DataValidationError
from app.data.cache import smart_cache
from app.ui.components import MetricsDisplay, Metric, KPICard, DistributionCharts, DataTable
from app.ui.layouts import PageLayout, SectionLayout
from app.utils import DataValidator, DataCleaner

# Legacy imports for compatibility
from app.core.logging import performance_monitor, log_cache_performance, app_logger
from app.core.exceptions import ErrorHandler, DataFetchError, safe_operation

# Get configuration
settings = get_settings()

@log_cache_performance  
@performance_monitor
async def fetch_os_data_async(filters_dict: dict = None) -> Tuple:
    """Busca dados de ordens de serviço e métricas."""
    
    try:
        client = ArkmedsClient.from_session()
        
        # Use os filtros passados ou os padrão para OS
        if filters_dict is None:
            from datetime import date
            filters = {
                "dt_ini": date.today().replace(day=1),
                "dt_fim": date.today(),
                "estado_ids": [],
            }
        else:
            filters = filters_dict
        
        # Extrair datas e outros filtros
        dt_ini = filters.get("dt_ini")
        dt_fim = filters.get("dt_fim") 
        estado_ids = filters.get("estado_ids", [])
        
        # Preparar filtros para a API (manter compatibilidade)
        api_filters = {}
        if estado_ids:
            api_filters["estado_ids"] = estado_ids
        
        # Buscar métricas e OS em paralelo
        metrics_task = compute_metrics(client, start_date=dt_ini, end_date=dt_fim, **api_filters)
        
        # Para list_os, usar o filtro correto
        os_filters = {
            "data_criacao__gte": dt_ini,
            "data_criacao__lte": dt_fim,
        }
        # Testar diferentes formatos para filtro de estado
        if estado_ids:
            # Aumentar page_size quando há filtros para compensar filtragem local
            os_filters["page_size"] = 100  
            # Armazenar o estado_ids para filtragem local
            os_filters["_local_filter_estados"] = estado_ids
            # Tentar primeiro com estado__in (padrão Django)
            os_filters["estado__in"] = estado_ids
            
        os_raw_task = client.list_os(**os_filters)
        
        metrics, os_raw = await asyncio.gather(metrics_task, os_raw_task)
        
        # Validar dados se existirem
        if os_raw:
            df = pd.DataFrame([o.model_dump() for o in os_raw])
            df = DataValidator.validate_dataframe(
                df, 
                required_columns=["id", "chamados"],
                name="Ordens de Serviço"
            )
        
        return metrics, os_raw
        
    except Exception as e:
        app_logger.log_error(e, {"context": "fetch_os_data_async"})
        raise APIError(f"Erro ao buscar dados: {str(e)}")


# Wrapper function for compatibility  
@smart_cache(ttl=900)
def fetch_os_data(filters_dict: dict = None) -> Tuple:
    """Wrapper síncrono para compatibilidade."""
    async def async_wrapper():
        return await fetch_os_data_async(filters_dict)
    return run_async_safe(async_wrapper())


def render_kpi_metrics(metrics) -> None:
    """Renderiza as métricas principais de KPI usando novos componentes."""
    
    if not metrics:
        st.warning("⚠️ Nenhuma métrica disponível")
        return
    
    # Preparar métricas para os novos componentes
    maintenance_metrics = [
        Metric(
            label="Corretivas (Predial)",
            value=getattr(metrics, 'corrective_building', 0),
            icon="�"
        ),
        Metric(
            label="Corretivas (Engenharia)",
            value=getattr(metrics, 'corrective_engineering', 0),
            icon="⚙️"
        ),
        Metric(
            label="Preventivas (Predial)",
            value=getattr(metrics, 'preventive_building', 0),
            icon="🔄"
        )
    ]
    
    operational_metrics = [
        Metric(
            label="Preventivas (Infra)",
            value=getattr(metrics, 'preventive_infra', 0),
            icon="🏗️"
        ),
        Metric(
            label="Busca Ativa",
            value=getattr(metrics, 'active_search', 0),
            icon="🔍"
        ),
        Metric(
            label="Abertas Atualmente", 
            value=getattr(metrics, 'currently_open', 0),
            icon="📋"
        )
    ]
    
    # KPI Cards
    kpi_cards = [
        KPICard(title="Manutenção Corretiva/Preventiva", metrics=maintenance_metrics),
        KPICard(title="Operações e Status", metrics=operational_metrics)
    ]
    
    MetricsDisplay.render_kpi_dashboard(kpi_cards)


def render_summary_chart(metrics) -> None:
    """Renderiza gráfico resumo de abertas vs fechadas usando novos componentes."""
    
    if not metrics:
        st.warning("⚠️ Nenhuma métrica disponível para o gráfico")
        return
    
    # Calcular totais
    abertas_total = getattr(metrics, 'backlog', 0)
    fechadas_total = (
        getattr(metrics, 'corrective_building', 0) +
        getattr(metrics, 'corrective_engineering', 0) +
        getattr(metrics, 'preventive_building', 0) +
        getattr(metrics, 'preventive_infra', 0) +
        getattr(metrics, 'active_search', 0)
    )
    
    # Criar DataFrame para o gráfico
    chart_data = pd.DataFrame({
        "Status": ["Abertas", "Fechadas"],
        "Quantidade": [abertas_total, fechadas_total]
    })
    
    # Usar novo componente de gráfico
    DistributionCharts.render_bar_chart(
        data=chart_data,
        x_col="Status",
        y_col="Quantidade", 
        title="📈 Resumo: Ordens Abertas vs Fechadas"
    )
    
    # Métricas de resumo
    total = abertas_total + fechadas_total
    if total > 0:
        summary_metrics = [
            Metric(
                label="Taxa de Resolução",
                value=f"{(fechadas_total/total)*100:.1f}%",
                icon="📈"
            ),
            Metric(
                label="Total de OS",
                value=total,
                icon="📊"
            )
        ]
        MetricsDisplay.render_metric_cards(summary_metrics, columns=2)


def render_os_table(os_raw: list) -> None:
    """Renderiza tabela detalhada de ordens de serviço usando novos componentes."""
    
    if not os_raw:
        st.info("Nenhuma ordem de serviço encontrada para os filtros selecionados.")
        return
    
    # Converter para DataFrame e limpar dados
    df = pd.DataFrame([o.model_dump() for o in os_raw])
    
    # Limpar dados usando utilitários
    for col in df.select_dtypes(include=['object']).columns:
        df = DataCleaner.clean_string_column(
            df, col, 
            strip_whitespace=True,
            remove_empty=True
        )
    
    # Converter tipos mistos para string para evitar problemas com Arrow
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
    
    # Usar novo componente de tabela
    table = (DataTable(data=df, title="📋 Lista de Ordens de Serviço")
        .add_filters(
            filterable_columns=["tipo", "status", "prioridade"] if "tipo" in df.columns else [],
            searchable_columns=["chamados", "descricao"] if "chamados" in df.columns else []
        )
    )
    
    # Adicionar filtro de data se disponível
    if "data_criacao" in df.columns:
        table = table.add_date_filter("data_criacao")
    
    # Formatar colunas se existirem
    column_formats = {}
    if "valor" in df.columns:
        column_formats["valor"] = "currency"
    if "tempo_resolucao" in df.columns:
        column_formats["tempo_resolucao"] = "duration"
    
    if column_formats:
        table = table.format_columns(column_formats)
    
    # Adicionar paginação e renderizar
    table.add_pagination(page_size=20).render()


def main():
    """Função principal da página de Ordem de Serviço."""
    st.set_page_config(
        page_title="Ordem de Serviço - Indicadores", 
        page_icon="📋",
        layout="wide"
    )
    
    # Inicializar cliente
    try:
        client = ArkmedsClient.from_session()
    except Exception as e:
        st.error(f"Erro ao conectar com o cliente Arkmeds: {str(e)}")
        st.info("Verifique as credenciais em .streamlit/secrets.toml")
        return
    
    # Renderizar filtros específicos de OS na sidebar
    filters = render_os_filters(client)
    
    # Layout principal
    layout = PageLayout(
        title="📋 Ordem de Serviço",
        description="Análise de ordens de serviço, KPIs de manutenção e SLA"
    )
    layout.render_header()
    
    # Adicionar botão para limpar cache (debug) no topo da página
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col4:
        if st.button("🔄 Limpar Cache & Atualizar", 
                    help="Remove dados em cache e força busca completa da API"):
            # Limpar cache do Streamlit
            st.cache_data.clear()
            # Limpar cache de sessão se houver
            if "_arkmeds_client" in st.session_state:
                del st.session_state["_arkmeds_client"]
            st.success("✅ Cache limpo! Recarregando dados...")
            st.rerun()
    
    with layout.main_content():
        # Mostrar filtros ativos
        show_os_active_filters(client)
        
        # Buscar dados com os filtros de OS
        try:
            result = fetch_os_data(filters)
            if result is None or len(result) != 2:
                st.error("Erro ao carregar dados. Verifique a conexão com a API.")
                return
            
            metrics, os_raw = result
            
            if metrics is None:
                st.error("Erro ao calcular métricas. Verifique os dados e filtros.")
                return
                
            if os_raw is None:
                os_raw = []
                
        except Exception as e:
            st.error(f"Erro inesperado ao carregar dados: {str(e)}")
            st.exception(e)  # Para debugging
            return
        
        # Renderizar seções com novos layouts
        with SectionLayout.metric_section("📊 KPIs de Manutenção"):
            render_kpi_metrics(metrics)
        
        with SectionLayout.chart_section("📈 Resumo Geral"):
            render_summary_chart(metrics)
        
        with SectionLayout.data_section("📋 Detalhes das Ordens"):
            render_os_table(os_raw)
# Executar a aplicação
if __name__ == "__main__":
    main()
