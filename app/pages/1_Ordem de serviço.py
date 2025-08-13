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
from app.ui.components.refresh_controls import render_refresh_controls, render_compact_refresh_button
from app.ui.layouts import PageLayout, SectionLayout
from app.utils import DataValidator, DataCleaner

# Legacy imports for compatibility
from app.core.logging import performance_monitor, log_cache_performance, app_logger
from app.core.exceptions import ErrorHandler, DataFetchError, safe_operation

# Get configuration
settings = get_settings()


def compute_metrics_from_sqlite_data(service_orders: dict, dt_ini, dt_fim) -> dict:
    """
    Processa métricas a partir de dados do SQLite.
    
    Função local otimizada que evita chamadas async desnecessárias
    quando os dados já estão carregados do banco local.
    """
    from app.services.os_metrics import OSMetrics
    
    try:
        # Extrair listas de ordens por categoria
        corretivas_predial = service_orders.get("corrective_building", [])
        corretivas_eng = service_orders.get("corrective_engineering", [])
        preventivas_predial = service_orders.get("preventive_building", [])
        preventivas_infra = service_orders.get("preventive_infra", [])
        busca_ativa = service_orders.get("active_search", [])
        abertas = service_orders.get("open_orders", [])
        fechadas = service_orders.get("closed_orders", [])
        
        # Calcular SLA
        sla_pct = 0.0
        if fechadas:
            from app.services.os_metrics import calculate_sla_metrics
            # Para SLA, usar função síncrona se disponível
            sla_pct = calculate_sla_sync(fechadas)
        
        # Criar objeto de métricas
        metrics = OSMetrics(
            corretivas_predial=len(corretivas_predial),
            corretivas_eng_clin=len(corretivas_eng),
            preventivas_predial=len(preventivas_predial),
            preventivas_infra=len(preventivas_infra),
            busca_ativa=len(busca_ativa),
            abertas=len(abertas),
            fechadas=len(fechadas),
            sla_pct=sla_pct
        )
        
        # Retornar dados completos
        return {
            'metrics': metrics,
            'service_orders': service_orders,
            'dt_ini': dt_ini,
            'dt_fim': dt_fim
        }
    
    except Exception as e:
        st.error(f"❌ Erro ao calcular métricas: {e}")
        return {}


def calculate_sla_sync(closed_orders: list) -> float:
    """Calcula SLA de forma síncrona para dados locais."""
    try:
        from datetime import datetime
        
        if not closed_orders:
            return 0.0
        
        sla_compliant = 0
        total_orders = len(closed_orders)
        sla_hours = 72  # SLA padrão de 72h
        
        for order in closed_orders:
            try:
                if not order.data_criacao or not order.data_fechamento:
                    continue
                
                # Parse dates
                if isinstance(order.data_criacao, str):
                    created = datetime.fromisoformat(order.data_criacao.replace('Z', '+00:00'))
                else:
                    created = order.data_criacao
                
                if isinstance(order.data_fechamento, str):
                    closed = datetime.fromisoformat(order.data_fechamento.replace('Z', '+00:00'))
                else:
                    closed = order.data_fechamento
                
                # Calcular diferença em horas
                diff_hours = (closed - created).total_seconds() / 3600
                
                if diff_hours <= sla_hours:
                    sla_compliant += 1
            
            except Exception:
                continue
        
        return round((sla_compliant / total_orders) * 100, 1) if total_orders > 0 else 0.0
    
    except Exception:
        return 0.0

@log_cache_performance  
@performance_monitor
async def fetch_os_data_async(filters_dict: dict = None) -> Tuple:
    """
    Busca dados de ordens de serviço - REFATORADO PARA SQLITE.
    
    🔄 NOVA IMPLEMENTAÇÃO: Leitura direta do SQLite local
    """
    
    try:
        # Compatibilidade: ainda aceita client mas não usa para busca principal
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
        
        # ========== NOVA ABORDAGEM: LEITURA DIRETA DO SQLITE ==========
        from app.services.repository import get_orders_df, get_database_stats
        
        st.info("💾 Carregando dados do SQLite local...")
        
        # Verificar estatísticas do banco
        stats = get_database_stats()
        orders_count = stats.get('orders_count', 0)
        
        if orders_count == 0:
            st.warning("📭 Banco local vazio. Executando sincronização inicial...")
            from app.services.sync.ingest import BackfillSync
            backfill = BackfillSync()
            await backfill.run_backfill(['orders'], batch_size=100)
            st.success("✅ Sincronização inicial concluída")
        
        # Verificar frescor e sincronizar se necessário
        from app.services.sync.delta import should_run_incremental_sync, run_incremental_sync
        
        if should_run_incremental_sync('orders', max_age_hours=2):
            st.info("🔄 Executando sincronização incremental...")
            await run_incremental_sync('orders')
            st.success("✅ Dados sincronizados")
        
        # Buscar dados otimizados do SQLite
        df = get_orders_df(
            start_date=dt_ini.isoformat(),
            end_date=dt_fim.isoformat(),
            estados=estado_ids,
            limit=5000
        )
        
        if df.empty:
            st.warning("📭 Nenhuma ordem encontrada no período especificado")
            return pd.DataFrame(), {}
        
        st.success(f"✅ {len(df):,} registros carregados do SQLite")
        
        # ========== PROCESSAR DADOS LOCALMENTE ==========
        # Converter para formato legacy para compatibilidade com compute_metrics
        from app.services.os_metrics import _convert_sqlite_df_to_service_orders
        
        try:
            service_orders = _convert_sqlite_df_to_service_orders(df, dt_ini, dt_fim, filters)
        except Exception as e:
            # Fallback para conversão antiga se nova falhar
            st.warning(f"⚠️ Usando conversão fallback: {e}")
            from app.services.os_metrics import _convert_df_to_service_orders
            service_orders = _convert_df_to_service_orders(df, dt_ini, dt_fim, filters)
        
        # Calcular métricas localmente (sem async necessário)
        metrics_data = compute_metrics_from_sqlite_data(service_orders, dt_ini, dt_fim)
        
        # Retornar dados no formato esperado
        # Extrair métricas e dados brutos do resultado
        metrics = metrics_data.get('metrics')
        os_raw = []
        
        # Converter service_orders de volta para lista de objetos para compatibilidade
        for category_orders in service_orders.values():
            if isinstance(category_orders, list):
                os_raw.extend(category_orders)
        
        return metrics, os_raw
        
    except Exception as e:
        # Fallback para API se SQLite falhar
        app_logger.log_error(e, {"context": "fetch_os_data_async (SQLite)"})
        st.warning(f"⚠️ Erro no SQLite: {e}")
        st.info("🔄 Tentando fallback para API...")
        
        try:
            # Usar função original como fallback
            api_filters = {}
            if estado_ids:
                api_filters["estado_ids"] = estado_ids
            
            # Buscar métricas da API
            metrics = await compute_metrics(client, start_date=dt_ini, end_date=dt_fim, **api_filters)
            
            # Buscar OS da API
            os_filters = {
                "data_criacao__gte": dt_ini,
                "data_criacao__lte": dt_fim,
            }
            if estado_ids:
                os_filters["page_size"] = 100  
                os_filters["_local_filter_estados"] = estado_ids
                os_filters["estado__in"] = estado_ids
            
            os_raw = await client.list_os(**os_filters)
            
            return metrics, os_raw
            
        except Exception as api_error:
            app_logger.log_error(api_error, {"context": "fetch_os_data_async (API fallback)"})
            raise APIError(f"Erro ao buscar dados (SQLite e API): {str(api_error)}")


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
    
    # ========== CONTROLES DE SINCRONIZAÇÃO NA SIDEBAR ==========
    with st.sidebar:
        st.markdown("---")
        render_compact_refresh_button(['orders'])
        
        # Status rápido
        with st.expander("📊 Status dos Dados"):
            from app.ui.components.refresh_controls import render_sync_status
            render_sync_status(['orders'], compact_mode=True)
    
    # Layout principal
    layout = PageLayout(
        title="📋 Ordem de Serviço",
        description="Análise de ordens de serviço, KPIs de manutenção e SLA"
    )
    layout.render_header()
    
    # ========== CONTROLES PRINCIPAIS DE SINCRONIZAÇÃO ==========
    st.markdown("### 🔄 Gerenciamento de Dados")
    
    # Abas para organizar melhor
    tab_dados, tab_filtros = st.tabs(["� Dados & Sincronização", "🎛️ Filtros Avançados"])
    
    with tab_dados:
        # Controles de refresh completos
        render_refresh_controls(
            resources=['orders'],
            show_advanced=True,
            compact_mode=False
        )
    
    with tab_filtros:
        # Mostrar filtros ativos para transparência
        show_os_active_filters(filters)
    
    st.markdown("---")
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
