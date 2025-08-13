"""
Página de Configurações centralizando gerenciamento de dados e agendamento.

Esta página centraliza:
- Gerenciamento de dados (migrado da página Ordem de Serviço)
- Sistema de agendamento automático (migrado da main)
"""

import sys
from pathlib import Path

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
    from core.logging import app_logger
    from core.scheduler import get_scheduler_status
    from services.repository import get_database_stats
    from ui.components.refresh_controls import render_refresh_controls, render_sync_status
    from ui.components.scheduler_status import render_scheduler_status
except ImportError:
    try:
        # Tentar importar com prefixo app. (quando executado do diretório raiz)
        from app.core.logging import app_logger
        from app.core.scheduler import get_scheduler_status
        from app.services.repository import get_database_stats
        from app.ui.components.refresh_controls import render_refresh_controls, render_sync_status
        from app.ui.components.scheduler_status import render_scheduler_status
    except ImportError as e:
        st.error(f"Erro ao importar módulos: {e}")
        st.stop()

# Configuração da página
st.set_page_config(page_title="Configurações", page_icon="⚙️", layout="wide")

st.title("⚙️ Configurações")
st.caption("Gerenciamento centralizado de dados e sistema de agendamento automático")

# Abas principais
tab_dados, tab_agendamento = st.tabs(["📊 Gerenciamento de Dados", "🕐 Agendamento Automático"])

# ========== ABA: GERENCIAMENTO DE DADOS ==========
with tab_dados:
    st.subheader("📊 Gerenciamento de Dados")
    st.caption(
        "Atualize dados manualmente, visualize status das sincronizações e gerencie o cache local"
    )

    # Sub-abas para organização
    subtab_sync, subtab_status = st.tabs(["🔄 Sincronização", "📈 Status dos Dados"])

    with subtab_sync:
        st.markdown("#### Controles de Sincronização")
        st.info(
            "💡 **Dica:** Use sincronização incremental para updates rápidos ou backfill completo para reconstrução total dos dados"
        )

        # Controles completos de sincronização para todos os recursos
        render_refresh_controls(
            resources=["orders", "equipments", "technicians"],
            show_advanced=True,
            compact_mode=False,
        )

    with subtab_status:
        st.markdown("#### Status Detalhado dos Dados")

        # Status compacto de sincronização
        render_sync_status(["orders", "equipments", "technicians"], compact_mode=False)

        # Estatísticas do banco de dados
        try:
            with st.expander("📊 Estatísticas do Banco de Dados"):
                stats = get_database_stats()
                if stats:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Ordens de Serviço",
                            f"{stats.get('orders_count', 0):,}",
                            help="Total de registros na tabela de ordens",
                        )

                    with col2:
                        st.metric(
                            "Equipamentos",
                            f"{stats.get('equipments_count', 0):,}",
                            help="Total de registros na tabela de equipamentos",
                        )

                    with col3:
                        st.metric(
                            "Técnicos",
                            f"{stats.get('technicians_count', 0):,}",
                            help="Total de registros na tabela de técnicos",
                        )

                    # Informações adicionais
                    if stats.get("last_updated"):
                        st.info(f"🕐 Última atualização: {stats['last_updated']}")

                else:
                    st.warning("⚠️ Não foi possível obter estatísticas do banco de dados")

        except Exception as e:
            st.error(f"❌ Erro ao obter estatísticas: {e}")
            app_logger.log_error(e, {"context": "settings_database_stats"})

        # Cache de leitura (se aplicável)
        with st.expander("🧹 Limpeza de Cache"):
            st.markdown("**Cache de Leitura do Streamlit**")
            st.caption("Limpa cache de queries e componentes para forçar recarga dos dados")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧹 Limpar Cache de Dados", use_container_width=True):
                    st.cache_data.clear()
                    st.success("✅ Cache de dados limpo")
                    st.rerun()

            with col2:
                if st.button("🔄 Limpar Cache de Recursos", use_container_width=True):
                    st.cache_resource.clear()
                    st.success("✅ Cache de recursos limpo")
                    st.rerun()

# ========== ABA: AGENDAMENTO AUTOMÁTICO ==========
with tab_agendamento:
    st.subheader("🕐 Sistema de Agendamento Automático")
    st.caption("Status do scheduler e controles de sincronização automática")

    # Status completo do scheduler
    try:
        render_scheduler_status(compact=False, show_controls=True)

        # Informações adicionais sobre o scheduler
        with st.expander("ℹ️ Informações do Sistema"):
            st.markdown(
                """
            **Como funciona o agendamento automático:**
            
            - 🔄 **Sincronização Incremental**: Busca apenas dados novos/alterados
            - ⏰ **Intervalo Configurável**: Definido em `secrets.toml` ou variáveis de ambiente
            - 🎯 **Recursos Monitorados**: Ordens de serviço, equipamentos e técnicos
            - 💾 **Persistência Local**: Dados armazenados em SQLite local
            - 📊 **Fallback Inteligente**: Se incremental falhar, executa backfill automático
            
            **Controles Disponíveis:**
            - ▶️ **Executar Agora**: Força sincronização imediata
            - 📈 **Backfill Completo**: Reconstrói base de dados do zero
            - ⏸️ **Pausar/Retomar**: Controla execução automática
            """
            )

            # Status técnico detalhado
            try:
                status = get_scheduler_status()
                st.json(status)
            except Exception as e:
                st.error(f"Erro ao obter status: {e}")

    except Exception as e:
        st.error(f"❌ Erro ao renderizar status do scheduler: {e}")
        app_logger.log_error(e, {"context": "settings_scheduler_status"})

# ========== SIDEBAR LINK ==========
# Adicionar atalho explícito na sidebar se navegação customizada existir
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔧 Administração")

    # Link para esta página (self-reference para destacar)
    if st.button("⚙️ Configurações", use_container_width=True, type="primary"):
        st.rerun()

    st.caption("Acesse esta página para gerenciar dados e agendamento")

# ========== RODAPÉ COM INFORMAÇÕES ==========
st.markdown("---")
with st.expander("📋 Sobre esta Página"):
    st.markdown(
        """
    **Configurações Centralizadas**
    
    Esta página centraliza todas as funcionalidades administrativas que antes estavam distribuídas:
    
    - **Gerenciamento de Dados** (antes na página Ordem de Serviço)
    - **Sistema de Agendamento** (antes na página principal)
    
    **Vantagens da centralização:**
    - ✅ Interface mais organizada
    - ✅ Controles administrativos em local dedicado  
    - ✅ Melhor experiência para usuários finais
    - ✅ Facilita manutenção e expansão futura
    """
    )
