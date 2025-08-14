import pathlib
import sys


ROOT = pathlib.Path(__file__).parent.parent  # Diretório raiz do projeto
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from app.core.db import get_database_info, init_database  # noqa: E402
from app.core.startup import ensure_startup_sync  # noqa: E402
from app.services.sync_jobs import get_last_success_job, get_running_job  # noqa: E402
from app.ui import register_pages  # noqa: E402


# Configure the main page
st.set_page_config(page_title="Tela Principal", page_icon="🏠", layout="wide")


# Initialize database and startup sync
@st.cache_resource
def initialize_app():
    """Inicializa componentes da aplicação uma única vez."""
    try:
        # Inicializar banco de dados
        init_database()

        # Inicializar scheduler automático
        from app.core.scheduler import initialize_scheduler

        scheduler = initialize_scheduler()

        if scheduler:
            from app.core.logging import app_logger

            app_logger.log_info("🕐 Sistema de agendamento automático iniciado")

        # Iniciar sincronização de startup
        ensure_startup_sync()

        return True
    except Exception as e:
        st.error(f"Erro ao inicializar aplicação: {e}")
        return False


# Initialize app components
if initialize_app():
    db_info = get_database_info()
    if db_info.get("database_exists"):
        st.success("✅ Banco de dados inicializado com sucesso")

    # Link para configurações administrativas
    with st.expander("⚙️ Configurações Administrativas"):
        st.info(
            """
        **Sistema de agendamento e gerenciamento de dados**
        
        Para acessar controles administrativos como:
        - Sistema de agendamento automático
        - Controles de sincronização  
        - Status detalhado dos dados
        
        Navegue até **⚙️ Configurações** usando o menu lateral.
        """
        )

        # Atalho direto (se disponível)
        if st.button("🔧 Acessar Configurações", use_container_width=True):
            st.switch_page("pages/Configuracoes.py")


def _render_sync_status():
    """Renderiza o status de sincronização de dados na página principal."""
    try:
        # Verificar se há job rodando
        running_job = get_running_job()

        if running_job:
            # Mostrar progresso ativo
            st.info("🔄 Sincronizando dados da API...")

            col1, col2 = st.columns([3, 1])

            with col1:
                if running_job.get("percent") is not None:
                    # Progresso determinado
                    progress_text = (
                        f"{running_job['processed']:,}/{running_job.get('total', '?'):,} itens"
                    )
                    st.progress(running_job["percent"] / 100.0, text=progress_text)
                else:
                    # Progresso indeterminado
                    with st.spinner(f"Processados {running_job['processed']:,} itens..."):
                        st.empty()  # Placeholder para spinner

            with col2:
                st.caption(f"🔄 {running_job['kind'].title()}")
                st.caption(f"⏰ {running_job['updated_at']}")

            # Auto-refresh quando há job rodando
            st_autorefresh(interval=3000, key="sync-progress")

        else:
            # Mostrar último status bem-sucedido
            last_success = get_last_success_job()

            if last_success:
                st.success("✅ Dados atualizados")

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.caption(f"📊 Última sincronização: {last_success.get('finished_at', 'N/A')}")
                    if last_success.get("processed"):
                        st.caption(f"📈 {last_success['processed']:,} registros sincronizados")

                with col2:
                    st.caption(f"🔄 {last_success['kind'].title()}")

            else:
                st.warning("⚠️ Nenhuma sincronização encontrada")
                st.caption("A sincronização será executada automaticamente.")

    except Exception as e:
        st.error(f"❌ Erro ao verificar status de sincronização: {e}")


# Initialize pages and global settings
register_pages()

# Main page content
st.header("📊 Indicadores")

# Mostrar status de sincronização de dados
_render_sync_status()

st.markdown(
    """
## Bem-vindo ao Dashboard de Indicadores COMG

Este dashboard apresenta indicadores consolidados da plataforma Arkmeds para análise de:

- **📋 Ordens de Serviço** - Análise de chamados e SLA
- **⚙️ Equipamentos** - MTTR, MTBF e disponibilidade  
- **👥 Técnicos** - Performance e produtividade da equipe

### 🚀 Como usar

1. **Navegue** pelas páginas usando o menu lateral
2. **Configure** os filtros específicos em cada página
3. **Visualize** os KPIs e gráficos interativos
4. **Analise** os dados detalhados nas tabelas
5. **Mantenha** dados atualizados com sincronização automática

### 📊 Páginas disponíveis

Use o menu lateral para navegar entre as diferentes análises disponíveis.

**💡 Dica:** O sistema sincroniza dados automaticamente em intervalos regulares. 
Você também pode usar os controles manuais de atualização em cada página.
"""
)
