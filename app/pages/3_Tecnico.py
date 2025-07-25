"""Página de análise de desempenho de técnicos."""

import asyncio
from typing import List, Tuple

import pandas as pd
import streamlit as st

from arkmeds_client.client import ArkmedsClient
from app.ui.utils import run_async_safe
from app.ui.filters import render_filters, show_active_filters

# Configuração da página
st.set_page_config(
    page_title="Técnicos", 
    page_icon="👷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constantes
CACHE_TTL_DEFAULT = 900  # 15 minutos


@st.cache_data(ttl=CACHE_TTL_DEFAULT, show_spinner="Carregando dados de técnicos...")
def fetch_technician_data() -> Tuple:
    """Busca dados de técnicos e suas atividades."""
    
    async def _fetch_data_async():
        client = ArkmedsClient.from_session()
        
        # Buscar dados de usuários/técnicos
        users_task = client.list_users()
        
        # Adicionar mais dados conforme necessário
        users = await users_task
        return users
    
    return run_async_safe(_fetch_data_async())


def render_technician_overview(users: List) -> None:
    """Renderiza visão geral dos técnicos."""
    st.header("👷 Visão Geral dos Técnicos")
    
    if not users:
        st.info("Nenhum técnico encontrado.")
        return
    
    # Métricas básicas
    total_technicians = len(users)
    active_technicians = len([u for u in users if getattr(u, 'ativo', True)])
    
    cols = st.columns(3)
    cols[0].metric("👥 Total de Técnicos", total_technicians)
    cols[1].metric("✅ Técnicos Ativos", active_technicians)
    cols[2].metric("📊 Taxa de Atividade", f"{(active_technicians/total_technicians)*100:.1f}%" if total_technicians > 0 else "0%")


def render_technician_table(users: List) -> None:
    """Renderiza tabela detalhada de técnicos."""
    st.header("📋 Lista de Técnicos")
    
    if not users:
        st.info("Nenhum técnico encontrado.")
        return
    
    # Converter para DataFrame
    df = pd.DataFrame([u.model_dump() for u in users])
    
    # Filtros da tabela
    col1, col2 = st.columns(2)
    with col1:
        if 'nome' in df.columns:
            search_term = st.text_input("🔍 Buscar por nome:", placeholder="Digite o nome do técnico...")
    
    with col2:
        if 'ativo' in df.columns:
            status_filter = st.selectbox("Filtrar por Status:", ["Todos", "Ativo", "Inativo"], index=0)
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if 'nome' in df.columns and search_term:
        filtered_df = filtered_df[filtered_df['nome'].str.contains(search_term, case=False, na=False)]
    
    if 'ativo' in df.columns and status_filter != "Todos":
        is_active = status_filter == "Ativo"
        filtered_df = filtered_df[filtered_df['ativo'] == is_active]
    
    # Exibir tabela
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=400,
        column_config={
            "nome": "Nome",
            "email": "E-mail",
            "ativo": st.column_config.CheckboxColumn("Ativo"),
        }
    )
    
    # Botão de download
    st.download_button(
        "⬇️ Baixar CSV",
        filtered_df.to_csv(index=False).encode(),
        "tecnicos.csv",
        mime="text/csv"
    )
    
    # Estatísticas da tabela
    if len(filtered_df) > 0:
        st.info(f"📊 Exibindo {len(filtered_df)} de {len(df)} técnicos")


def render_under_construction() -> None:
    """Renderiza seção em construção."""
    st.header("� Funcionalidades em Desenvolvimento")
    
    with st.expander("📈 Próximas funcionalidades"):
        st.markdown("""
        ### 🎯 Métricas de Performance
        - Número de OS por técnico
        - Tempo médio de resolução
        - Taxa de retrabalho
        - Avaliação de qualidade
        
        ### 📊 Análises Avançadas
        - Ranking de produtividade
        - Distribuição de tipos de serviço
        - Análise temporal de atividades
        - Comparação entre técnicos
        
        ### 🎨 Visualizações
        - Gráficos de barras comparativos
        - Heatmaps de atividades
        - Timeline de trabalho
        - Dashboard interativo
        """)


def main():
    """Função principal da página de técnicos."""
    st.title("�👷 Análise de Técnicos")
    
    # Renderizar filtros
    client = ArkmedsClient.from_session()
    render_filters(client)
    show_active_filters(client)
    
    # Buscar dados
    try:
        users = fetch_technician_data()
        
        # Renderizar seções
        render_technician_overview(users)
        st.divider()
        
        render_technician_table(users)
        st.divider()
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.info("Verifique sua conexão com a API.")
    
    render_under_construction()


# Executar a aplicação
main()
