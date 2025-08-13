"""
Componente de auto-refresh opcional como fallback para o scheduler.

Este módulo fornece funcionalidade de refresh automático da página
em intervalos longos, útil como fallback quando o scheduler não está ativo.
"""
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from app.core.logging import app_logger
from app.core.scheduler import get_scheduler_status


def render_autorefresh_fallback(
    interval_seconds: int = 1800,  # 30 minutos por padrão
    key: str = "main_autorefresh",
    show_controls: bool = False
) -> int | None:
    """
    Renderiza auto-refresh opcional como fallback do scheduler.
    
    Só é ativado se o scheduler não estiver rodando ou se o usuário optar.
    
    Args:
        interval_seconds: Intervalo em segundos para refresh
        key: Chave única para o componente
        show_controls: Se deve mostrar controles para o usuário
        
    Returns:
        Contador de refresh ou None se não ativo
    """
    try:
        # Verificar status do scheduler
        scheduler_status = get_scheduler_status()
        scheduler_active = scheduler_status.get('running', False)

        # Configurações no session state
        enabled_key = f"{key}_enabled"

        # Inicializar estado se necessário
        if enabled_key not in st.session_state:
            # Ativar por padrão apenas se scheduler não estiver rodando
            st.session_state[enabled_key] = not scheduler_active

        # Mostrar controles se solicitado
        if show_controls:
            _render_autorefresh_controls(
                interval_seconds,
                enabled_key,
                scheduler_active
            )

        # Executar auto-refresh se habilitado
        if st.session_state.get(enabled_key, False):
            counter = st_autorefresh(
                interval=interval_seconds * 1000,  # Converter para ms
                key=key,
                debounce=False,
                limit=None
            )

            # Log do refresh
            if counter > 0:
                app_logger.log_info(
                    f"🔄 Auto-refresh executado (#{counter})",
                    interval_seconds=interval_seconds,
                    page_key=key
                )

            return counter

        return None

    except Exception as e:
        app_logger.log_error(e, {"context": "autorefresh_fallback"})
        return None


def _render_autorefresh_controls(
    interval_seconds: int,
    enabled_key: str,
    scheduler_active: bool
) -> None:
    """Renderiza controles do auto-refresh."""

    st.markdown("### 🔄 Auto-Refresh da Página")

    # Status do scheduler
    if scheduler_active:
        st.info("✅ Scheduler ativo - sincronização automática em segundo plano")
    else:
        st.warning("⚠️ Scheduler inativo - considere usar auto-refresh da página")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Toggle para ativar/desativar
        current_state = st.session_state.get(enabled_key, False)

        new_state = st.checkbox(
            f"Atualizar página a cada {interval_seconds // 60} minutos",
            value=current_state,
            help="Recarrega a página automaticamente para atualizar dados",
            key=f"{enabled_key}_toggle"
        )

        if new_state != current_state:
            st.session_state[enabled_key] = new_state
            st.rerun()

    with col2:
        if st.session_state.get(enabled_key, False):
            st.success("🟢 Ativo", icon="✅")
        else:
            st.error("🔴 Inativo", icon="❌")

    # Informações adicionais
    with st.expander("ℹ️ Como funciona"):
        st.markdown(f"""
        **Auto-Refresh da Página:**
        - Recarrega toda a página a cada {interval_seconds // 60} minutos
        - Força nova busca de dados do cache/banco
        - Útil como backup quando scheduler não está ativo
        - Consome mais recursos que o scheduler em segundo plano
        
        **Recomendação:**
        - Use apenas em páginas com alto tráfego
        - Prefira o scheduler automático quando possível
        - Considere intervalos longos (30+ minutos) para reduzir carga
        """)


def render_smart_refresh(
    page_name: str,
    high_traffic: bool = False,
    interval_minutes: int = 30
) -> None:
    """
    Renderiza sistema inteligente de refresh.
    
    Escolhe automaticamente entre scheduler e auto-refresh baseado no contexto.
    
    Args:
        page_name: Nome da página para logging
        high_traffic: Se é página de alto tráfego
        interval_minutes: Intervalo em minutos para auto-refresh
    """
    try:
        scheduler_status = get_scheduler_status()
        scheduler_active = scheduler_status.get('running', False)

        # Se scheduler ativo, apenas mostrar status
        if scheduler_active:
            interval_scheduler = scheduler_status.get('interval_minutes', 15)
            next_run = scheduler_status.get('next_run')

            st.success(
                f"🕐 Dados atualizados automaticamente a cada {interval_scheduler} minutos",
                icon="✅"
            )

            if next_run:
                try:
                    if isinstance(next_run, str):
                        next_run_dt = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
                    else:
                        next_run_dt = next_run

                    delta = next_run_dt - datetime.now()
                    if delta.total_seconds() > 0:
                        mins = int(delta.total_seconds() / 60)
                        st.caption(f"Próxima atualização em {mins} minutos")
                except:
                    pass

            return

        # Se scheduler inativo e página de alto tráfego, oferecer auto-refresh
        if high_traffic and not scheduler_active:
            st.warning("⚠️ Scheduler inativo - habilitando auto-refresh da página")

            counter = render_autorefresh_fallback(
                interval_seconds=interval_minutes * 60,
                key=f"autorefresh_{page_name}",
                show_controls=True
            )

            if counter and counter > 0:
                st.info(f"🔄 Página atualizada automaticamente (#{counter})")

        # Para páginas normais, apenas mostrar aviso
        else:
            st.info("ℹ️ Use os controles de sincronização para atualizar dados manualmente")

    except Exception as e:
        app_logger.log_error(e, {"context": "smart_refresh", "page": page_name})
        st.error("❌ Erro no sistema de refresh automático")


def render_autorefresh_badge() -> None:
    """Renderiza badge pequeno do auto-refresh para sidebar."""
    try:
        # Verificar se algum auto-refresh está ativo
        refresh_keys = [key for key in st.session_state.keys() if "_autorefresh_enabled" in key]
        any_active = any(st.session_state.get(key, False) for key in refresh_keys)

        if any_active:
            st.sidebar.info("🔄 Auto-refresh ativo", icon="🟢")

    except Exception as e:
        app_logger.log_error(e, {"context": "render_autorefresh_badge"})
