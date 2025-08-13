"""
Componente de status do scheduler automático.

Exibe informações sobre o agendamento de sincronizações e permite controle manual.
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

from app.core.scheduler import get_scheduler_status, initialize_scheduler
from app.core.logging import app_logger


def render_scheduler_status(
    compact: bool = False, 
    show_controls: bool = True
) -> None:
    """
    Renderiza status do scheduler automático.
    
    Args:
        compact: Se True, exibe versão compacta
        show_controls: Se deve mostrar controles de start/stop
    """
    try:
        status = get_scheduler_status()
        
        if compact:
            _render_compact_status(status)
        else:
            _render_full_status(status, show_controls)
            
    except Exception as e:
        st.error(f"❌ Erro ao verificar scheduler: {e}")
        app_logger.log_error(e, {"context": "render_scheduler_status"})


def _render_compact_status(status: dict) -> None:
    """Renderiza versão compacta do status."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if status['running']:
            st.success(
                f"🕐 Auto-sync ativo ({status['interval_minutes']}min)", 
                icon="✅"
            )
        else:
            st.warning("⏸️ Auto-sync pausado", icon="⚠️")
    
    with col2:
        if status['last_run']:
            last_run = status['last_run']
            if isinstance(last_run, str):
                try:
                    last_run = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
                except:
                    pass
            
            # Calcular tempo desde última execução
            if isinstance(last_run, datetime):
                delta = datetime.now() - last_run.replace(tzinfo=None)
                if delta.total_seconds() < 60:
                    time_str = "agora"
                elif delta.total_seconds() < 3600:
                    time_str = f"{int(delta.total_seconds() / 60)}m"
                else:
                    time_str = f"{int(delta.total_seconds() / 3600)}h"
                
                st.caption(f"Última: {time_str}")


def _render_full_status(status: dict, show_controls: bool) -> None:
    """Renderiza versão completa do status."""
    
    # Header
    st.subheader("🕐 Agendamento Automático")
    
    # Status principal
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        if status['running']:
            st.success("✅ **Status:** Ativo")
            if status['interval_minutes']:
                st.info(f"🔄 **Intervalo:** {status['interval_minutes']} minutos")
        else:
            st.error("❌ **Status:** Inativo")
            if 'error' in status:
                st.error(f"**Erro:** {status['error']}")
    
    with col2:
        if status['last_run']:
            last_run = _parse_datetime(status['last_run'])
            if last_run:
                st.write(f"⏰ **Última execução:**")
                st.write(last_run.strftime("%d/%m %H:%M"))
                
                if status['last_result']:
                    if "sucesso" in str(status['last_result']).lower():
                        st.success(f"✅ {status['last_result']}")
                    elif "erro" in str(status['last_result']).lower():
                        st.error(f"❌ {status['last_result']}")
                    else:
                        st.warning(f"⚠️ {status['last_result']}")
        else:
            st.write("⏰ **Última execução:** Nunca")
    
    with col3:
        if status['next_run']:
            next_run = _parse_datetime(status['next_run'])
            if next_run:
                st.write(f"⏭️ **Próxima execução:**")
                st.write(next_run.strftime("%d/%m %H:%M"))
                
                # Tempo até próxima execução
                delta = next_run - datetime.now()
                if delta.total_seconds() > 0:
                    minutes = int(delta.total_seconds() / 60)
                    if minutes < 60:
                        st.caption(f"em {minutes} minutos")
                    else:
                        hours = int(minutes / 60)
                        remaining_minutes = minutes % 60
                        st.caption(f"em {hours}h {remaining_minutes}m")
        else:
            st.write("⏭️ **Próxima execução:** -")
    
    # Controles (se habilitados)
    if show_controls:
        st.divider()
        _render_scheduler_controls(status)
    
    # Informações adicionais
    with st.expander("ℹ️ Informações do Sistema"):
        st.write("**Como funciona:**")
        st.write("• O scheduler executa sincronizações incrementais automaticamente")
        st.write("• Funciona apenas enquanto há sessões ativas no Streamlit")  
        st.write("• Em caso de sobreposição, execuções são combinadas (coalesce=True)")
        st.write("• O intervalo é configurável via secrets.toml ou variável de ambiente")
        
        if status.get('interval_minutes'):
            st.write(f"• **Intervalo atual:** {status['interval_minutes']} minutos")


def _render_scheduler_controls(status: dict) -> None:
    """Renderiza controles do scheduler."""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🚀 Reiniciar Scheduler", help="Reinicia o agendamento automático"):
            try:
                scheduler = initialize_scheduler()
                if scheduler:
                    st.rerun()
                else:
                    st.error("Falha ao reiniciar scheduler")
            except Exception as e:
                st.error(f"Erro ao reiniciar: {e}")
    
    with col2:
        if st.button("🔄 Executar Agora", help="Executa sincronização manualmente"):
            try:
                with st.spinner("Executando sincronização..."):
                    # Importar e executar sync
                    import asyncio
                    from app.services.sync.delta import run_incremental_sync
                    
                    # Executar de forma assíncrona
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(run_incremental_sync())
                    
                    if result:
                        st.success("✅ Sincronização executada com sucesso!")
                    else:
                        st.warning("⚠️ Sincronização concluída com avisos")
                    
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Erro na sincronização manual: {e}")
                app_logger.log_error(e, {"context": "manual_sync_from_scheduler_ui"})
    
    with col3:
        if st.button("📊 Atualizar Status", help="Atualiza informações do status"):
            st.rerun()


def _parse_datetime(dt_value) -> Optional[datetime]:
    """Parse datetime de diferentes formatos."""
    if not dt_value:
        return None
    
    if isinstance(dt_value, datetime):
        return dt_value.replace(tzinfo=None)
    
    if isinstance(dt_value, str):
        try:
            # Tentar ISO format
            return datetime.fromisoformat(dt_value.replace('Z', '+00:00')).replace(tzinfo=None)
        except:
            try:
                # Tentar formato padrão
                return datetime.strptime(dt_value, "%Y-%m-%d %H:%M:%S")
            except:
                return None
    
    return None


def render_scheduler_badge() -> None:
    """Renderiza badge pequeno do scheduler para sidebar."""
    try:
        status = get_scheduler_status()
        
        if status['running']:
            st.sidebar.success(
                f"🕐 Auto-sync ({status['interval_minutes']}m)", 
                icon="✅"
            )
            
            # Mostrar próxima execução se disponível
            if status['next_run']:
                next_run = _parse_datetime(status['next_run'])
                if next_run:
                    delta = next_run - datetime.now()
                    if delta.total_seconds() > 0:
                        minutes = int(delta.total_seconds() / 60)
                        st.sidebar.caption(f"Próxima em {minutes}min")
        else:
            st.sidebar.warning("⏸️ Auto-sync pausado", icon="⚠️")
            
    except Exception as e:
        st.sidebar.error("❌ Scheduler erro", icon="🔴")
        app_logger.log_error(e, {"context": "render_scheduler_badge"})
