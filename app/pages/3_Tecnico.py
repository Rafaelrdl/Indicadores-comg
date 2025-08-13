# -*- coding: utf-8 -*-
"""Página de análise de desempenho de técnicos usando nova arquitetura."""

import asyncio
from typing import List, Tuple

import pandas as pd
import streamlit as st

from app.arkmeds_client.client import ArkmedsClient
from app.ui.utils import run_async_safe
from app.ui.filters import render_filters, show_active_filters

# Nova arquitetura de componentes
from app.ui.components import MetricsDisplay, KPICard, DataTable, TimeSeriesCharts, DistributionCharts
from app.ui.layouts import PageLayout, SectionLayout
from app.data.cache import smart_cache
from app.data.validators import DataValidator

# Core imports
from app.core import get_settings, APIError, DataValidationError
from app.services.tech_metrics import compute_metrics, calculate_technician_kpis, TechnicianKPI


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
        from app.ui.components.refresh_controls import render_compact_refresh_button, render_sync_status
        render_compact_refresh_button(['technicians', 'orders'])
        
        # Status dos dados
        with st.expander("📊 Status"):
            render_sync_status(['technicians', 'orders'], compact_mode=True)
    
    # Usar novo sistema de layout
    layout = PageLayout(
        title="Análise de Técnicos", 
        description="Desempenho e atividades da equipe técnica",
        icon="👷"
    )
    
    layout.render_header()
    
    with layout.main_content():
        # Renderizar filtros (manter funcionalidade existente)
        client = ArkmedsClient.from_session()
        render_filters(client)
        show_active_filters(client)
        
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
                st.markdown("""
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
                """)
                
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")


async def fetch_technician_data() -> List[dict]:
    """Busca dados dos técnicos com cache inteligente."""
    try:
        client = ArkmedsClient.from_session()
        users = await client.list_users()
        
        # Converter para DataFrame e validar
        if users:
            df = pd.DataFrame([user.model_dump() for user in users])
            df = DataValidator.validate_dataframe(
                df, 
                required_columns=["id", "nome"],
                name="Técnicos"
            )
            return df.to_dict('records')
        
        return []
        
    except APIError as e:
        st.error("❌ Erro na API de usuários")
        raise e
    except DataValidationError as e:
        st.error("⚠️ Dados de usuários inválidos")
        raise e


@smart_cache(ttl=900)
def fetch_technician_data_cached() -> List[dict]:
    """Wrapper síncrono com cache para fetch_technician_data."""
    async def async_wrapper():
        return await fetch_technician_data()
    return run_async_safe(async_wrapper())


def render_technician_overview(users: List[dict]) -> None:
    """Renderiza visão geral dos técnicos com novos componentes."""
    
    # KPIs principais
    total_techs = len(users) if users else 0
    active_techs = len([u for u in users if u.get('is_active', True)]) if users else 0
    avg_experience = calculate_avg_experience(users)
    
    # Usar novos componentes KPI
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        KPICard.render(
            title="Total de Técnicos",
            value=total_techs,
            icon="👷",
            color="primary"
        )
    
    with col2:
        KPICard.render(
            title="Técnicos Ativos",
            value=active_techs,
            icon="✅",
            color="success"
        )
    
    with col3:
        rate = (active_techs/total_techs*100) if total_techs > 0 else 0
        KPICard.render(
            title="Taxa de Atividade",
            value=f"{rate:.1f}%",
            icon="📊",
            color="info"
        )
    
    with col4:
        KPICard.render(
            title="Experiência Média",
            value=f"{avg_experience:.1f} anos",
            icon="🎯",
            color="warning"
        )


def render_technician_table(users: List[dict]) -> None:
    """Renderiza tabela de técnicos com novo componente DataTable."""
    
    if not users:
        st.warning("📭 Nenhum técnico encontrado")
        return
    
    # Preparar dados para tabela
    df = pd.DataFrame(users)
    
    # Configurar colunas da tabela
    column_config = {
        'name': st.column_config.TextColumn("Nome", width="medium"),
        'email': st.column_config.TextColumn("Email", width="large"),
        'role': st.column_config.TextColumn("Função", width="small"),
        'is_active': st.column_config.CheckboxColumn("Ativo", width="small"),
        'last_login': st.column_config.DatetimeColumn("Último Login", width="medium")
    }
    
    # Usar novo componente DataTable
    DataTable.render(
        data=df,
        column_config=column_config,
        searchable_columns=['name', 'email'],
        filterable_columns=['role', 'is_active'],
        height=400
    )


def calculate_avg_experience(users: List[dict]) -> float:
    """Calcula experiência média dos técnicos."""
    if not users:
        return 0.0
    
    experiences = []
    for user in users:
        # Simular cálculo de experiência baseado em data de criação
        created_date = user.get('date_joined')
        if created_date:
            # Lógica simplificada - em produção usar datas reais
            experiences.append(2.5)  # Média simulada
    
    return sum(experiences) / len(experiences) if experiences else 0.0


# Executar função principal
if __name__ == "__main__":
    main()
