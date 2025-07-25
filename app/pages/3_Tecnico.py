"""PÃ¡gina de anÃ¡lise de desempenho de tÃ©cnicos usando nova arquitetura."""

import asyncio
from typing import List, Tuple

import pandas as pd
        show_stats=True
    )


def main():
    """FunÃ§Ã£o principal da pÃ¡gina de tÃ©cnicos usando nova arquitetura."""
    
    # Usar novo sistema de layout
    layout = PageLayout(
        title="AnÃ¡lise de TÃ©cnicos", 
        description="Desempenho e atividades da equipe tÃ©cnica",
        icon="ðŸ‘·"
    )
    
    layout.render_header()
    
    with layout.main_content():
        # Renderizar filtros (manter funcionalidade existente)
        client = ArkmedsClient.from_session()
        render_filters(client)
        show_active_filters(client)
        
        # Buscar dados
        try:
            users = fetch_technician_data()
            
            # Renderizar seÃ§Ãµes com novos layouts
            with SectionLayout.metric_section("ðŸ“Š VisÃ£o Geral da Equipe"):
                render_technician_overview(users)
            
            with SectionLayout.data_section("ðŸ“‹ Lista de TÃ©cnicos"):
                render_technician_table(users)
            
            # SeÃ§Ã£o em construÃ§Ã£o  
            with SectionLayout.info_section("ðŸš§ Funcionalidades em Desenvolvimento"):
                st.markdown("""
                ### ðŸŽ¯ MÃ©tricas de Performance
                - NÃºmero de OS por tÃ©cnico
                - Tempo mÃ©dio de resoluÃ§Ã£o
                - Taxa de retrabalho
                - AvaliaÃ§Ã£o de qualidade
                
                ### ðŸ“Š AnÃ¡lises AvanÃ§adas
                - Ranking de produtividade
                - DistribuiÃ§Ã£o de tipos de serviÃ§o
                - AnÃ¡lise temporal de atividades
                - ComparaÃ§Ã£o entre tÃ©cnicos
                
                ### ðŸŽ¨ VisualizaÃ§Ãµes
                - GrÃ¡ficos de barras comparativos
                - Heatmaps de atividades
                - Timeline de trabalho
                - Dashboard interativo
                """)
            
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            st.info("Verifique sua conexÃ£o com a API.")


# Executar a aplicaÃ§Ã£o
if __name__ == "__main__":
    main()streamlit as st

from arkmeds_client.client import ArkmedsClient
from app.ui.utils import run_async_safe
from app.ui.filters import render_filters, show_active_filters

# Nova arquitetura de componentes
from app.ui.components import MetricsDisplay, KPICard, DataTable, Charts
from app.ui.layouts import PageLayout, SectionLayout
from app.data.cache import smart_cache
from app.data.validators import DataValidator
from app.data.models import Metric
from app.utils.settings import get_settings

# ConfiguraÃ§Ã£o da pÃ¡gina
st.set_page_config(
    page_title="TÃ©cnicos", 
    page_icon="ðŸ‘·", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ConfiguraÃ§Ãµes globais
settings = get_settings()


@smart_cache(ttl=settings.cache.default_ttl)
def fetch_technician_data() -> Tuple:
    """Busca dados de tÃ©cnicos e suas atividades usando nova arquitetura."""
    
    async def _fetch_data_async():
        client = ArkmedsClient.from_session()
        
        # Buscar dados de usuÃ¡rios/tÃ©cnicos
        users_task = client.list_users()
        
        # Adicionar mais dados conforme necessÃ¡rio
        users = await users_task
        
        # Validar dados
        validator = DataValidator()
        users = validator.validate_list(users, required_fields=['id', 'nome'])
        
        return users
    
    return run_async_safe(_fetch_data_async())


def render_technician_overview(users: List) -> None:
    """Renderiza visÃ£o geral dos tÃ©cnicos usando nova arquitetura."""
    
    if not users:
        st.warning("Nenhum tÃ©cnico encontrado.")
        return
    
    # Calcular mÃ©tricas bÃ¡sicas
    total_technicians = len(users)
    active_technicians = len([u for u in users if getattr(u, 'ativo', True)])
    inactive_technicians = total_technicians - active_technicians
    activity_rate = (active_technicians/total_technicians)*100 if total_technicians > 0 else 0
    
    # MÃ©tricas de status
    status_metrics = [
        Metric(
            label="Total de TÃ©cnicos",
            value=str(total_technicians),
            icon="ðŸ‘¥"
        ),
        Metric(
            label="TÃ©cnicos Ativos",
            value=str(active_technicians),
            icon="âœ…"
        ),
        Metric(
            label="TÃ©cnicos Inativos",
            value=str(inactive_technicians),
            icon="âŒ"
        ),
        Metric(
            label="Taxa de Atividade",
            value=f"{activity_rate:.1f}%",
            icon="ðŸ“Š"
        )
    ]
    
    # KPI Cards
    kpi_cards = [
        KPICard(title="Status da Equipe TÃ©cnica", metrics=status_metrics)
    ]
    
    MetricsDisplay.render_kpi_dashboard(kpi_cards)


def render_technician_table(users: List) -> None:
    """Renderiza tabela detalhada de tÃ©cnicos usando nova arquitetura DataTable."""
    
    if not users:
        st.warning("Nenhum tÃ©cnico encontrado.")
        return
    
    # Preparar dados para a nova DataTable
    table_data = []
    for user in users:
        # Status baseado na atividade
        is_active = getattr(user, 'ativo', True)
        status = "Ativo" if is_active else "Inativo"
        status_color = "green" if is_active else "red"
        
        table_data.append({
            'ID': getattr(user, 'id', ''),
            'Nome': getattr(user, 'nome', ''),
            'Email': getattr(user, 'email', ''),
            'Status': status,
            'Status_Color': status_color,
            'Data CriaÃ§Ã£o': getattr(user, 'created_at', ''),
            'Ãšltimo Acesso': getattr(user, 'last_login', 'N/A')
        })
    
    # Configurar filtros para a DataTable
    table_config = {
        'columns': [
            {'key': 'ID', 'label': 'ID', 'width': 80},
            {'key': 'Nome', 'label': 'Nome', 'width': 200},
            {'key': 'Email', 'label': 'E-mail', 'width': 200},
            {'key': 'Status', 'label': 'Status', 'width': 100, 'color_column': 'Status_Color'},
            {'key': 'Data CriaÃ§Ã£o', 'label': 'Data CriaÃ§Ã£o', 'width': 120},
            {'key': 'Ãšltimo Acesso', 'label': 'Ãšltimo Acesso', 'width': 120}
        ],
        'filters': [
            {'column': 'Status', 'type': 'multiselect'}
        ],
        'searchable_columns': ['Nome', 'Email'],
        'sortable': True,
        'pagination': True,
        'page_size': 15
    }
    
    # Renderizar usando novo DataTable
    data_table = DataTable()
    data_table.render(
        data=table_data,
        config=table_config,
        show_download=True,
        show_stats=True
    )


