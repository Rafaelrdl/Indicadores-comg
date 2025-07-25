import asyncio
import pandas as pd
import streamlit as st
from arkmeds_client.client import ArkmedsClient
from app.ui.utils import run_async_safe

st.set_page_config(page_title="Equipamentos", page_icon="🛠️", layout="wide")

st.title("🛠️ Equipamentos")

@st.cache_data(ttl=900)
def fetch_equipment_data(v: int):
    """Busca dados básicos dos equipamentos."""
    
    async def _fetch_data_async():
        client = ArkmedsClient.from_session()
        try:
            equip_list = await client.list_equipamentos()
            return equip_list
        except Exception as e:
            st.error(f"Erro ao carregar equipamentos: {e}")
            return []
    
    return run_async_safe(_fetch_data_async())

# Buscar dados
with st.spinner("Carregando dados de equipamentos…"):
    equip_list = fetch_equipment_data(1)

if equip_list:
    st.success(f"✅ Carregados {len(equip_list)} equipamentos")
    
    # Métricas básicas
    st.header("📊 Resumo dos Equipamentos")
    
    total_equipamentos = len(equip_list)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Equipamentos", total_equipamentos)
    
    with col2:
        # Contar por status se disponível
        ativos = sum(1 for eq in equip_list if hasattr(eq, 'ativo') and eq.ativo)
        st.metric("Ativos", ativos if ativos > 0 else "N/A")
    
    with col3:
        # Contar equipamentos com prioridade se disponível
        com_prioridade = sum(1 for eq in equip_list if hasattr(eq, 'prioridade') and eq.prioridade)
        st.metric("Com Prioridade", com_prioridade if com_prioridade > 0 else "N/A")
    
    with col4:
        # Contar equipamentos por empresa
        empresas = set()
        for eq in equip_list:
            if hasattr(eq, 'empresa') and eq.empresa:
                empresas.add(eq.empresa.get('nome', 'N/A') if isinstance(eq.empresa, dict) else str(eq.empresa))
        st.metric("Empresas", len(empresas) if empresas else "N/A")
    
    # Tabela de equipamentos
    st.header("📋 Lista de Equipamentos")
    
    # Converter para DataFrame
    data = []
    for eq in equip_list:
        row = {
            "ID": getattr(eq, 'id', 'N/A'),
            "Nome": getattr(eq, 'nome', 'N/A'),
            "Fabricante": getattr(eq, 'fabricante', 'N/A'),
            "Modelo": getattr(eq, 'modelo', 'N/A'),
            "Patrimônio": getattr(eq, 'patrimonio', 'N/A'),
            "Número de Série": getattr(eq, 'numero_serie', 'N/A'),
        }
        
        # Adicionar prioridade se disponível
        if hasattr(eq, 'prioridade'):
            prioridade = getattr(eq, 'prioridade', None)
            if prioridade:
                prioridade_map = {1: "Baixa", 2: "Normal", 3: "Alta", 4: "Urgente", 5: "Emergencial"}
                row["Prioridade"] = prioridade_map.get(prioridade, f"Nível {prioridade}")
            else:
                row["Prioridade"] = "Não definida"
        
        # Adicionar empresa se disponível
        if hasattr(eq, 'empresa') and eq.empresa:
            if isinstance(eq.empresa, dict):
                row["Empresa"] = eq.empresa.get('nome', 'N/A')
            else:
                row["Empresa"] = str(eq.empresa)
        else:
            row["Empresa"] = "N/A"
        
        data.append(row)
    
    if data:
        df = pd.DataFrame(data)
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            if "Empresa" in df.columns:
                empresas_unicas = sorted(df["Empresa"].unique())
                empresa_filtro = st.selectbox("Filtrar por Empresa", ["Todas"] + empresas_unicas)
                if empresa_filtro != "Todas":
                    df = df[df["Empresa"] == empresa_filtro]
        
        with col2:
            if "Prioridade" in df.columns:
                prioridades_unicas = sorted(df["Prioridade"].unique())
                prioridade_filtro = st.selectbox("Filtrar por Prioridade", ["Todas"] + prioridades_unicas)
                if prioridade_filtro != "Todas":
                    df = df[df["Prioridade"] == prioridade_filtro]
        
        # Exibir tabela
        st.dataframe(df, use_container_width=True)
        
        # Download CSV
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name="equipamentos.csv",
            mime="text/csv"
        )
    else:
        st.warning("Nenhum equipamento encontrado ou erro na estrutura dos dados.")
else:
    st.error("❌ Não foi possível carregar os equipamentos.")
