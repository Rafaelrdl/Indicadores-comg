"""Página de análise de equipamentos e manutenção."""

import asyncio
from collections import defaultdict
from datetime import date, datetime
from statistics import mean
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st
from dateutil.relativedelta import relativedelta

from arkmeds_client.client import ArkmedsClient
from arkmeds_client.models import Chamado
from config.os_types import TIPO_CORRETIVA
from services.equip_metrics import compute_metrics
from services.equip_advanced_metrics import (
    calcular_stats_equipamentos,
    calcular_mttf_mtbf_top,
    exibir_distribuicao_prioridade,
    exibir_distribuicao_status,
    exibir_top_mttf_mtbf,
)
from app.ui.utils import run_async_safe

# New infrastructure imports
from app.core import get_settings, APIError, DataValidationError
from app.data.cache import smart_cache
from app.ui.components import (
    MetricsDisplay, Metric, KPICard, TimeSeriesCharts, 
    DistributionCharts, KPICharts, DataTable
)
from app.ui.layouts import PageLayout, SectionLayout, GridLayout
from app.utils import DataValidator, DataCleaner, MetricsCalculator, DataTransformer

# Legacy imports for compatibility
from app.core.logging import performance_monitor, log_cache_performance, app_logger
from app.core.exceptions import ErrorHandler, DataFetchError, safe_operation

# Get configuration
settings = get_settings()


def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse date string no formato DD/MM/YY - HH:MM para datetime."""
    return DataTransformer.parse_arkmeds_datetime(date_str)


def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse date string no formato DD/MM/YY - HH:MM para datetime."""
    return DataTransformer.parse_arkmeds_datetime(date_str)


def _build_history_df(os_list: list[Chamado]) -> pd.DataFrame:
    """Constrói DataFrame com histórico de MTTR e MTBF por mês."""
    mttr_map: dict[date, list[float]] = defaultdict(list)
    by_eq: dict[int | None, list[Chamado]] = defaultdict(list)
    
    # Agrupar por equipamento e calcular MTTR
    for os_obj in os_list:
        data_fechamento_str = os_obj.ordem_servico.get("data_fechamento") if os_obj.ordem_servico else None
        if not data_fechamento_str:
            continue
        
        data_criacao = parse_datetime(os_obj.data_criacao_os)
        data_fechamento = parse_datetime(data_fechamento_str)
        
        if not data_criacao or not data_fechamento:
            continue
            
        month = data_fechamento.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        delta_h = (data_fechamento - data_criacao).total_seconds() / 3600
        mttr_map[month].append(delta_h)
        by_eq[os_obj.equipamento_id].append(os_obj)

    # Calcular MTBF
    mtbf_map: dict[date, list[float]] = defaultdict(list)
    for items in by_eq.values():
        if len(items) < 2:
            continue
            
        items.sort(key=lambda o: parse_datetime(o.data_criacao_os) or datetime.min)
        
        for i in range(1, len(items)):
            current_date = parse_datetime(items[i].data_criacao_os)
            previous_date = parse_datetime(items[i-1].data_criacao_os)
            
            if not current_date or not previous_date:
                continue
                
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


@smart_cache(ttl=settings.cache.default_ttl)
@log_cache_performance
@performance_monitor
async def fetch_equipment_data_async() -> tuple:
    """Busca dados básicos de equipamentos e histórico de manutenção."""
    
    try:
        client = ArkmedsClient.from_session()
        
        # Período fixo dos últimos 12 meses para equipamentos
        dt_fim = date.today()
        dt_ini = dt_fim - relativedelta(months=12)
        
        # Buscar métricas e equipamentos primeiro (mais simples)
        metrics_task = compute_metrics(client, start_date=dt_ini, end_date=dt_fim)
        equip_task = client.list_equipment()
        
        # Buscar os dados básicos primeiro
        metrics, equip_list = await asyncio.gather(metrics_task, equip_task)
        
        # Buscar histórico separadamente para evitar problemas
        try:
            os_hist = await client.list_chamados({"tipo_id": TIPO_CORRETIVA})
        except Exception as e:
            app_logger.warning(f"Erro ao buscar histórico de chamados: {e}")
            os_hist = []
        
        # Validar dados
        if equip_list:
            df = pd.DataFrame([e.model_dump() for e in equip_list])
            df = DataValidator.validate_dataframe(
                df, 
                required_columns=["id", "nome"],
                name="Equipamentos"
            )
        
        return metrics, equip_list, os_hist
        
    except Exception as e:
        app_logger.error(f"Erro na busca de dados de equipamentos: {e}")
        raise APIError(f"Erro ao buscar dados de equipamentos: {str(e)}")


# Wrapper function for compatibility
def fetch_equipment_data() -> tuple:
    """Wrapper síncrono para compatibilidade."""
    return run_async_safe(fetch_equipment_data_async())


@smart_cache(ttl=settings.cache.heavy_operations_ttl)
@log_cache_performance
async def fetch_advanced_stats_async():
    """Busca estatísticas avançadas dos equipamentos."""
    try:
        return await calcular_stats_equipamentos(ArkmedsClient.from_session())
    except Exception as e:
        app_logger.error(f"Erro ao calcular stats avançadas: {e}")
        return None


def fetch_advanced_stats():
    """Wrapper síncrono para compatibilidade."""
    return run_async_safe(fetch_advanced_stats_async())


@smart_cache(ttl=settings.cache.heavy_operations_ttl)
@log_cache_performance
@performance_monitor
async def fetch_mttf_mtbf_data_async():
    """Busca dados de MTTF/MTBF (operação pesada)."""
    try:
        return await calcular_mttf_mtbf_top(ArkmedsClient.from_session())
    except Exception as e:
        app_logger.error(f"Erro ao calcular MTTF/MTBF: {e}")
        return ([], [])


def fetch_mttf_mtbf_data():
    """Wrapper síncrono para compatibilidade."""
    return run_async_safe(fetch_mttf_mtbf_data_async())


def render_basic_metrics(metrics, equip_list: list) -> None:
    """Renderiza as métricas básicas de equipamentos usando novos componentes."""
    
    # Verificar se métricas são válidas
    if metrics is None:
        st.warning("⚠️ Métricas não disponíveis.")
        return

    # Calcular métricas derivadas
    pct_em_manut = round(metrics.em_manutencao / metrics.ativos * 100, 1) if metrics.ativos else 0
    idades = [
        (date.today() - eq.data_aquisicao.date()).days / 365
        for eq in equip_list
        if eq.data_aquisicao
    ]
    idade_media = round(mean(idades), 1) if idades else 0

    # Preparar métricas para os novos componentes
    status_metrics = [
        Metric(
            label="Equipamentos Ativos",
            value=getattr(metrics, 'ativos', 0),
            icon="🔋"
        ),
        Metric(
            label="Desativados",
            value=getattr(metrics, 'desativados', 0),
            icon="🚫"
        ),
        Metric(
            label="Em Manutenção",
            value=f"{getattr(metrics, 'em_manutencao', 0)} ({pct_em_manut}%)",
            icon="🔧"
        ),
        Metric(
            label="MTTR Médio",
            value=f"{getattr(metrics, 'mttr_h', 0):.1f}h",
            icon="⏱️"
        )
    ]
    
    performance_metrics = [
        Metric(
            label="MTBF Médio",
            value=f"{getattr(metrics, 'mtbf_h', 0):.1f}h",
            icon="📈"
        ),
        Metric(
            label="Disponibilidade",
            value=f"{getattr(metrics, 'disponibilidade', 0):.1f}%",
            icon="📊"
        ),
        Metric(
            label="Idade Média do Parque",
            value=f"{idade_media} anos",
            icon="📅"
        ),
        Metric(
            label="% Em Manutenção",
            value=f"{pct_em_manut}%",
            icon="🔧"
        )
    ]

    # KPI Cards
    kpi_cards = [
        KPICard(title="Status dos Equipamentos", metrics=status_metrics),
        KPICard(title="Performance e Disponibilidade", metrics=performance_metrics)
    ]
    
    MetricsDisplay.render_kpi_dashboard(kpi_cards)
    
    cols = st.columns(3)
    cols[0].metric("🔄 MTBF (h)", metrics.mtbf_h)
    cols[1].metric("⚠️ % Ativos EM", pct_em_manut)
    cols[2].metric("📅 Idade média", idade_media)


def render_advanced_analysis() -> None:
    """Renderiza a análise avançada de equipamentos."""
    st.header("📈 Análise Avançada de Equipamentos")

    try:
        advanced_stats = fetch_advanced_stats()
        
        # Sub-seções da análise avançada
        st.subheader("🔋 Status dos Equipamentos")
        exibir_distribuicao_status(advanced_stats)

        st.subheader("🎯 Distribuição de Prioridade")
        exibir_distribuicao_prioridade(advanced_stats)
        
    except Exception as e:
        st.error(f"Erro ao carregar análise avançada: {e}")


def render_maintenance_history(os_hist: list[Chamado]) -> None:
    """Renderiza o histórico de manutenção (MTTR vs MTBF)."""
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
        fig.update_layout(
            xaxis_title="Mês",
            yaxis_title="Horas",
            legend_title="Métrica"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não há dados suficientes para gerar o histórico de manutenção.")


def render_reliability_rankings() -> None:
    """Renderiza os rankings de confiabilidade (MTTF/MTBF)."""
    st.header("🏆 Top Rankings de Confiabilidade")

    # Informações sobre os cálculos
    with st.expander("ℹ️ Sobre os cálculos de MTTF/MTBF"):
        st.info("""
        **MTTF (Mean Time To Failure)**: Tempo médio até a primeira falha após aquisição.
        Equipamentos com maior MTTF são mais confiáveis.
        
        **MTBF (Mean Time Between Failures)**: Tempo médio entre falhas consecutivas.
        Equipamentos com maior MTBF têm maior disponibilidade.
        
        ⚠️ **Nota**: Este cálculo pode demorar alguns minutos pois analisa o histórico completo
        de manutenções de todos os equipamentos.
        """)

    # Controle para habilitar cálculo pesado
    calcular_rankings = st.checkbox(
        "🔄 Calcular Rankings MTTF/MTBF",
        help="Este cálculo pode demorar alguns minutos. Deixe marcado apenas se necessário."
    )

    if calcular_rankings:
        try:
            top_mttf, top_mtbf = fetch_mttf_mtbf_data()
            exibir_top_mttf_mtbf(top_mttf, top_mtbf)
        except Exception as e:
            st.error(f"Erro ao calcular rankings: {e}")
            st.info("Tente novamente em alguns minutos.")

def _build_equipment_table(equip_list: list, os_hist: list[Chamado]) -> pd.DataFrame:
    """Constrói tabela detalhada de equipamentos com métricas individuais."""
    df = pd.DataFrame([e.model_dump() for e in equip_list])
    df["status"] = df["ativo"].map({True: "Ativo", False: "Desativado"})
    df["idade_anos"] = df["data_aquisicao"].apply(
        lambda d: round((date.today() - d.date()).days / 365, 1) if d else None
    )
    
    # Agrupar chamados por equipamento
    by_eq: dict[int, list[Chamado]] = defaultdict(list)
    for os_obj in os_hist:
        data_fechamento_str = os_obj.ordem_servico.get("data_fechamento") if os_obj.ordem_servico else None
        if os_obj.equipamento_id is not None and data_fechamento_str:
            by_eq[os_obj.equipamento_id].append(os_obj)
    
    # Calcular métricas por equipamento
    mttr_local = []
    mtbf_local = []
    ultima_os = []
    
    for eq in df["id"]:
        items = by_eq.get(eq, [])
        if items:
            # Obter datas de fechamento válidas
            datas_fechamento = []
            for o in items:
                data_fechamento_str = o.ordem_servico.get("data_fechamento")
                if data_fechamento_str:
                    data_fechamento = parse_datetime(data_fechamento_str)
                    if data_fechamento:
                        datas_fechamento.append(data_fechamento)
            
            if datas_fechamento:
                ultima_os.append(max(datas_fechamento).date())
                
                # Calcular MTTR
                tempos_reparo = []
                for o in items:
                    data_criacao = parse_datetime(o.data_criacao_os)
                    data_fechamento_str = o.ordem_servico.get("data_fechamento")
                    if data_fechamento_str:
                        data_fechamento = parse_datetime(data_fechamento_str)
                        if data_criacao and data_fechamento:
                            tempo_reparo = (data_fechamento - data_criacao).total_seconds()
                            tempos_reparo.append(tempo_reparo)
                
                mttr_local.append(
                    round(mean(tempos_reparo) / 3600, 2) if tempos_reparo else 0.0
                )
                
                # Calcular MTBF
                if len(items) > 1:
                    items.sort(key=lambda o: parse_datetime(o.data_criacao_os) or datetime.min)
                    intervals = []
                    for i in range(1, len(items)):
                        data_atual = parse_datetime(items[i].data_criacao_os)
                        data_anterior = parse_datetime(items[i-1].data_criacao_os)
                        if data_atual and data_anterior:
                            interval = (data_atual - data_anterior).total_seconds()
                            intervals.append(interval)
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


def render_equipment_table(equip_list: list, os_hist: list[Chamado]) -> None:
    """Renderiza tabela de equipamentos usando nova arquitetura DataTable."""
    
    if not equip_list:
        st.warning("Nenhum equipamento encontrado.")
        return
    
    # Preparar dados para a nova DataTable
    table_data = []
    for equip in equip_list:
        # Calcular métricas básicas do equipamento
        equip_os = [os for os in os_hist if os.get('equipamento_id') == equip.get('id')]
        total_os = len(equip_os)
        
        # Status baseado no número de ordens
        if total_os == 0:
            status = "Normal"
            status_color = "green"
        elif total_os <= 3:
            status = "Atenção"
            status_color = "orange"
        else:
            status = "Crítico"
            status_color = "red"
            
        # Calcular idade se disponível
        idade = 0
        if hasattr(equip, 'data_aquisicao') and equip.data_aquisicao:
            idade = round((date.today() - equip.data_aquisicao.date()).days / 365, 1)
            
        table_data.append({
            'ID': equip.get('id', ''),
            'Equipamento': equip.get('nome', ''),
            'Setor': equip.get('setor', {}).get('nome', 'N/A'),
            'Marca': equip.get('marca', {}).get('nome', 'N/A'),
            'Modelo': equip.get('modelo', ''),
            'Idade (anos)': idade,
            'Ordens Abertas': total_os,
            'Status': status,
            'Status_Color': status_color
        })
    
    # Configurar filtros para a DataTable
    table_config = {
        'columns': [
            {'key': 'ID', 'label': 'ID', 'width': 80},
            {'key': 'Equipamento', 'label': 'Equipamento', 'width': 200},
            {'key': 'Setor', 'label': 'Setor', 'width': 150},
            {'key': 'Marca', 'label': 'Marca', 'width': 120},
            {'key': 'Modelo', 'label': 'Modelo', 'width': 150},
            {'key': 'Idade (anos)', 'label': 'Idade (anos)', 'width': 100},
            {'key': 'Ordens Abertas', 'label': 'Ordens Abertas', 'width': 120},
            {'key': 'Status', 'label': 'Status', 'width': 100, 'color_column': 'Status_Color'}
        ],
        'filters': [
            {'column': 'Setor', 'type': 'multiselect'},
            {'column': 'Marca', 'type': 'multiselect'},
            {'column': 'Status', 'type': 'multiselect'}
        ],
        'searchable_columns': ['Equipamento', 'Modelo'],
        'sortable': True,
        'pagination': True,
        'page_size': 20
    }
    
    # Renderizar usando novo DataTable
    data_table = DataTable()
    data_table.render(
        data=table_data,
        config=table_config,
        show_download=True,
        show_stats=True
    )


def main():
    """Função principal da página de equipamentos usando nova arquitetura."""
    
    # Usar novo sistema de layout
    layout = PageLayout(
        title="Análise de Equipamentos", 
        description="Métricas de MTTR, MTBF e confiabilidade dos equipamentos",
        icon="🛠️"
    )
    
    layout.render_header()
    
    with layout.main_content():
        # Buscar dados
        try:
            result = fetch_equipment_data()
            if result is None or len(result) != 3:
                st.error("Erro ao carregar dados de equipamentos. Verifique a conexão com a API.")
                return
            
            metrics, equip_list, os_hist = result
            
            if metrics is None:
                st.error("Erro ao calcular métricas de equipamentos. Verifique os dados.")
                return
                
            if equip_list is None:
                equip_list = []
                
            if os_hist is None:
                os_hist = []
                
        except Exception as e:
            st.error(f"Erro inesperado ao carregar dados de equipamentos: {str(e)}")
            return
        
        # Renderizar seções com novos layouts
        with SectionLayout.metric_section("📊 Métricas Básicas de Equipamentos"):
            render_basic_metrics(metrics, equip_list)
        
        with SectionLayout.chart_section("📈 Análise Avançada"):
            render_advanced_analysis()
        
        with SectionLayout.chart_section("🔧 Histórico de Manutenção"):
            render_maintenance_history(os_hist)
        
        with SectionLayout.chart_section("🏆 Rankings de Confiabilidade"):
            render_reliability_rankings()
        
        with SectionLayout.data_section("📋 Tabela de Equipamentos"):
            render_equipment_table(equip_list, os_hist)


# Executar a aplicação
if __name__ == "__main__":
    main()
            render_equipment_table(equip_list, os_hist)


# Executar a aplicação
if __name__ == "__main__":
    main()
