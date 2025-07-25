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
from app.core.logging import performance_monitor, log_cache_performance, app_logger
from app.core.exceptions import ErrorHandler, DataFetchError, safe_operation

# Configuração da página
st.set_page_config(
    page_title="Equipamentos", 
    page_icon="🛠️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constantes
CACHE_TTL_DEFAULT = 900  # 15 minutos
CACHE_TTL_HEAVY = 1800   # 30 minutos para operações pesadas
DEFAULT_PERIOD_MONTHS = 12


def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse date string no formato DD/MM/YY - HH:MM para datetime."""
    try:
        return datetime.strptime(date_str, "%d/%m/%y - %H:%M")
    except (ValueError, TypeError):
        return None


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


@st.cache_data(ttl=CACHE_TTL_DEFAULT, show_spinner="Carregando dados de equipamentos...")
@log_cache_performance
@performance_monitor
def fetch_equipment_data() -> tuple:
    """Busca dados básicos de equipamentos e histórico de manutenção."""
    
    @safe_operation(
        fallback_value=(None, [], []),
        error_message="Erro ao buscar dados de equipamentos"
    )
    def _safe_fetch():
        async def _fetch_data_async():
            client = ArkmedsClient.from_session()
            
            # Período fixo dos últimos 12 meses para equipamentos
            dt_fim = date.today()
            dt_ini = dt_fim - relativedelta(months=DEFAULT_PERIOD_MONTHS)
            
            # Buscar métricas, equipamentos e histórico em paralelo
            metrics_task = compute_metrics(client, start_date=dt_ini, end_date=dt_fim)
            equip_task = client.list_equipment()
            os_hist_task = client.list_chamados({"tipo_id": TIPO_CORRETIVA})
            
            return await asyncio.gather(metrics_task, equip_task, os_hist_task)
        
        return run_async_safe(_fetch_data_async())
    
    return _safe_fetch()


@st.cache_data(ttl=CACHE_TTL_DEFAULT, show_spinner="Carregando estatísticas avançadas...")
@log_cache_performance
def fetch_advanced_stats():
    """Busca estatísticas avançadas dos equipamentos."""
    return ErrorHandler.safe_execute(
        lambda: calcular_stats_equipamentos(ArkmedsClient.from_session()),
        fallback_value=None,
        error_message="Erro ao carregar estatísticas avançadas"
    )


@st.cache_data(ttl=CACHE_TTL_HEAVY, show_spinner="Calculando MTTF/MTBF... Pode demorar alguns minutos...")
@log_cache_performance
@performance_monitor
def fetch_mttf_mtbf_data():
    """Busca dados de MTTF/MTBF (operação pesada)."""
    return ErrorHandler.safe_execute(
        lambda: calcular_mttf_mtbf_top(ArkmedsClient.from_session()),
        fallback_value=([], []),
        error_message="Erro ao calcular rankings MTTF/MTBF"
    )


def render_basic_metrics(metrics, equip_list: list) -> None:
    """Renderiza as métricas básicas de equipamentos."""
    st.header("📊 Métricas Básicas de Equipamentos")

    # Calcular métricas derivadas
    pct_em_manut = round(metrics.em_manutencao / metrics.ativos * 100, 1) if metrics.ativos else 0
    idades = [
        (date.today() - eq.data_aquisicao.date()).days / 365
        for eq in equip_list
        if eq.data_aquisicao
    ]
    idade_media = round(mean(idades), 1) if idades else 0

    # Exibir métricas em colunas
    cols = st.columns(4)
    cols[0].metric("🔋 Ativos", metrics.ativos)
    cols[1].metric("🚫 Desativados", metrics.desativados)
    cols[2].metric("🔧 Em manutenção", metrics.em_manutencao)
    cols[3].metric("⏱️ MTTR (h)", metrics.mttr_h)
    
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
    """Renderiza a tabela detalhada de equipamentos."""
    st.header("📋 Lista Detalhada de Equipamentos")
    
    df = _build_equipment_table(equip_list, os_hist)
    
    # Filtros da tabela
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Filtrar por Status:",
            ["Todos", "Ativo", "Desativado"],
            index=0
        )
    
    with col2:
        idade_min = st.number_input("Idade mínima (anos):", min_value=0.0, value=0.0, step=0.1)
    
    with col3:
        idade_max = st.number_input("Idade máxima (anos):", min_value=0.0, value=50.0, step=0.1)
    
    # Aplicar filtros
    filtered_df = df.copy()
    if status_filter != "Todos":
        filtered_df = filtered_df[filtered_df["status"] == status_filter]
    
    if "idade_anos" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["idade_anos"].fillna(0) >= idade_min) & 
            (filtered_df["idade_anos"].fillna(0) <= idade_max)
        ]
    
    # Exibir tabela
    st.dataframe(
        filtered_df, 
        height=500, 
        use_container_width=True,
        column_config={
            "id": "ID",
            "nome": "Nome",
            "status": "Status",
            "idade_anos": st.column_config.NumberColumn(
                "Idade (anos)",
                format="%.1f"
            ),
            "ultima_os": "Última OS",
            "mttr_local": st.column_config.NumberColumn(
                "MTTR (h)",
                format="%.2f"
            ),
            "mtbf_local": st.column_config.NumberColumn(
                "MTBF (h)",
                format="%.2f"
            ),
        }
    )
    
    # Download
    st.download_button(
        "⬇️ Baixar CSV", 
        filtered_df.to_csv(index=False).encode(), 
        "equipamentos.csv",
        mime="text/csv"
    )


def main():
    """Função principal da página de equipamentos."""
    st.title("🛠️ Análise de Equipamentos")
    
    # Buscar dados
    metrics, equip_list, os_hist = fetch_equipment_data()
    
    # Renderizar seções
    render_basic_metrics(metrics, equip_list)
    st.divider()
    
    render_advanced_analysis()
    st.divider()
    
    render_maintenance_history(os_hist)
    st.divider()
    
    render_reliability_rankings()
    st.divider()
    
    render_equipment_table(equip_list, os_hist)


# Executar a aplicação
main()
