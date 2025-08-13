import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import streamlit as st
from arkmeds_client.client import ArkmedsClient
from app.ui import register_pages  # noqa: E402
from app.core.db import init_database, get_database_info  # noqa: E402

# Configure the main page
st.set_page_config(page_title="Tela Principal", page_icon="🏠", layout="wide")

# Initialize database on first run
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
        
        return True
    except Exception as e:
        st.error(f"Erro ao inicializar aplicação: {e}")
        return False

# Initialize app components
if initialize_app():
    db_info = get_database_info()
    if db_info.get('database_exists'):
        st.success("✅ Banco de dados inicializado com sucesso")
    
    # Mostrar status do scheduler na página principal
    from app.ui.components.scheduler_status import render_scheduler_status
    with st.expander("🕐 Sistema de Agendamento Automático"):
        render_scheduler_status(show_controls=True)

# Initialize pages and global settings
register_pages()

# Main page content
st.header("📊 Indicadores")

st.markdown("""
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
""")
