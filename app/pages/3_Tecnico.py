"""Página de análise de desempenho de técnicos usando nova arquitetura."""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# Configuração de imports flexível para diferentes contextos de execução
current_dir = Path(__file__).parent
app_dir = current_dir.parent
root_dir = app_dir.parent

# Adicionar paths necessários
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Imports flexíveis que funcionam em diferentes contextos
try:
    # Tentar importar sem prefixo app. (quando executado do diretório app)
    from arkmeds_client.client import ArkmedsClient
    from services.repository import get_technicians_df
    from ui.components import (
        DataTable,
        DistributionCharts,
        KPICard,
        MetricsDisplay,
        TimeSeriesCharts,
    )
    from ui.filters import render_filters, show_active_filters
    from ui.utils import run_async_safe
except ImportError:
    try:
        # Tentar importar com prefixo app. (quando executado do diretório raiz)
        from app.arkmeds_client.client import ArkmedsClient
        from app.services.repository import get_technicians_df
        from app.ui.components import (
            DataTable,
            DistributionCharts,
            KPICard,
            MetricsDisplay,
            TimeSeriesCharts,
        )
        from app.ui.filters import render_filters, show_active_filters
        from app.ui.utils import run_async_safe
    except ImportError as e:
        st.error(f"Erro ao importar módulos: {e}")
        st.stop()
# Core imports
from app.core import DataValidationError
from app.core.logging import app_logger
from app.data.validators import DataValidator
from app.ui.layouts import PageLayout, SectionLayout


def main():
    """Função principal da página de técnicos usando nova arquitetura."""

    # ========== CONTROLES NA SIDEBAR ==========
    with st.sidebar:
        st.markdown("---")

        # Badge do scheduler automático
        from app.ui.components.scheduler_status import render_scheduler_badge

        render_scheduler_badge()

        st.markdown("---")

        st.markdown("**🔄 Sincronização**")
        from app.ui.components.refresh_controls import (
            render_compact_refresh_button,
            render_sync_status,
        )

        render_compact_refresh_button(["technicians", "orders"])

        # Status dos dados
        with st.expander("📊 Status"):
            render_sync_status(["technicians", "orders"], compact_mode=True)

    # Usar novo sistema de layout
    layout = PageLayout(
        title="Análise de Técnicos",
        description="Desempenho e atividades da equipe técnica",
        icon="👷",
    )

    layout.render_header()

    with layout.main_content():
        # Status: Temporariamente removendo renderização de filtros API
        # TODO: Implementar filtros baseados em dados do Repository
        st.info("🔧 Filtros em migração - usando dados locais do SQLite")

        # Buscar dados
        try:
            users = fetch_technician_data_cached()

            # Renderizar seções com novos layouts
            with SectionLayout.metric_section("📊 Visão Geral da Equipe"):
                render_technician_overview(users)

            with SectionLayout.data_section("📋 Lista de Técnicos"):
                render_technician_table(users)

            # Seção em construção
            with SectionLayout.info_section("🚧 Funcionalidades em Desenvolvimento"):
                st.markdown(
                    """
                ### 🎯 Métricas de Performance
                - **Produtividade por Técnico**: Ordens concluídas por período
                - **Tempo Médio de Resolução**: MTTR por tipo de ordem
                - **Eficiência por Localização**: Performance geográfica
                - **Análise de Competências**: Especialização por equipamento
                
                ### 📈 Dashboards Avançados
                - **Heatmaps de Atividade**: Visualização temporal
                - **Ranking de Performance**: Comparativo entre técnicos
                - **Alertas de Produtividade**: Notificações automáticas
                
                ### 🎮 Gamificação
                - **Sistema de Pontos**: Recompensas por performance
                - **Badges de Conquista**: Reconhecimento de especialização
                - **Leaderboards**: Rankings motivacionais
                """
                )

        except Exception as e:
            st.error(f"Erro ao carregar dados: {e!s}")


async def fetch_technician_data() -> list[dict]:
    """Busca dados dos técnicos usando Repository (SQLite local)."""
    try:
        # Usar Repository em vez da API
        technicians_df = get_technicians_df()

        # Converter para lista de dicts e validar
        if not technicians_df.empty:
            # Validar DataFrame
            technicians_df = DataValidator.validate_dataframe(
                technicians_df, required_columns=["id", "nome"], name="Técnicos"
            )
            return technicians_df.to_dict("records")

        return []

    except DataValidationError as e:
        st.error("⚠️ Dados de técnicos inválidos")
        app_logger.log_error(e, {"context": "technician_validation"})
        raise e
    except Exception as e:
        st.error("❌ Erro ao buscar dados de técnicos")
        app_logger.log_error(e, {"context": "fetch_technician_data_repository"})
        return []


def fetch_technician_data_cached() -> list[dict]:
    """Busca dados de técnicos do banco local em vez da API."""
    try:
        app_logger.log_info("👷 Buscando dados de técnicos do SQLite local...")

        # ========== NOVA ABORDAGEM: LEITURA DIRETA DO SQLITE ==========
        from app.services.repository import get_database_stats, get_technicians_df

        # Verificar estatísticas do banco
        stats = get_database_stats()
        technicians_count = stats.get("technicians_count", 0)

        # Se banco está vazio, avisar usuário para executar sincronização
        if technicians_count == 0:
            st.warning(
                """
            📭 **Dados não encontrados no banco local**
            
            Para visualizar os dados de técnicos, é necessário executar a sincronização inicial.
            Use os controles na sidebar ou aguarde a sincronização automática.
            """
            )
            return []

        # Buscar técnicos do SQLite
        technicians_df = get_technicians_df(limit=500)

        if technicians_df.empty:
            st.warning("📭 Nenhum técnico encontrado no banco local")
            return []

        # Converter technicians_df para lista de dicts compatíveis
        technicians_list = []
        for _, row in technicians_df.iterrows():
            try:
                payload = (
                    json.loads(row["payload"])
                    if isinstance(row["payload"], str)
                    else row["payload"]
                )
                technicians_list.append(
                    {
                        "id": payload.get("id"),
                        "nome": payload.get("nome", ""),
                        "email": payload.get("email", ""),
                        "ativo": payload.get("ativo", True),
                        "is_active": payload.get("ativo", True),  # Compatibilidade
                        **payload,  # Incluir todos os outros campos
                    }
                )
            except Exception as e:
                app_logger.log_error(e, {"context": "processar_tecnico"})
                continue

        app_logger.log_info(f"✅ Carregados {len(technicians_list)} técnicos do SQLite")
        return technicians_list

    except Exception as e:
        app_logger.log_error(e, {"context": "fetch_technician_data_cached_sqlite"})
        st.error(f"⚠️ Erro ao carregar dados: {e!s}")
        return []


def render_technician_overview(users: list[dict]) -> None:
    """Renderiza visão geral dos técnicos com novos componentes."""

    # KPIs principais
    total_techs = len(users) if users else 0
    active_techs = len([u for u in users if u.get("is_active", True)]) if users else 0
    avg_experience = calculate_avg_experience(users)

    # Usar novos componentes KPI
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        KPICard.render(title="Total de Técnicos", value=total_techs, icon="👷", color="primary")

    with col2:
        KPICard.render(title="Técnicos Ativos", value=active_techs, icon="✅", color="success")

    with col3:
        rate = (active_techs / total_techs * 100) if total_techs > 0 else 0
        KPICard.render(title="Taxa de Atividade", value=f"{rate:.1f}%", icon="📊", color="info")

    with col4:
        KPICard.render(
            title="Experiência Média",
            value=f"{avg_experience:.1f} anos",
            icon="🎯",
            color="warning",
        )


def render_technician_table(users: list[dict]) -> None:
    """Renderiza tabela de técnicos com novo componente DataTable."""

    if not users:
        st.warning("📭 Nenhum técnico encontrado")
        return

    # Preparar dados para tabela
    df = pd.DataFrame(users)

    # Configurar colunas da tabela
    column_config = {
        "name": st.column_config.TextColumn("Nome", width="medium"),
        "email": st.column_config.TextColumn("Email", width="large"),
        "role": st.column_config.TextColumn("Função", width="small"),
        "is_active": st.column_config.CheckboxColumn("Ativo", width="small"),
        "last_login": st.column_config.DatetimeColumn("Último Login", width="medium"),
    }

    # Usar novo componente DataTable
    DataTable.render(
        data=df,
        column_config=column_config,
        searchable_columns=["name", "email"],
        filterable_columns=["role", "is_active"],
        height=400,
    )


def calculate_avg_experience(users: list[dict]) -> float:
    """Calcula experiência média dos técnicos."""
    if not users:
        return 0.0

    experiences = []
    for user in users:
        # Simular cálculo de experiência baseado em data de criação
        created_date = user.get("date_joined")
        if created_date:
            # Lógica simplificada - em produção usar datas reais
            experiences.append(2.5)  # Média simulada

    return sum(experiences) / len(experiences) if experiences else 0.0


# Executar função principal
if __name__ == "__main__":
    main()
