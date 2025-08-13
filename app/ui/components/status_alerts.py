"""
Componente de notificação de status geral dos dados.

Este módulo fornece alertas e notificações sobre o estado
geral da sincronização em todas as páginas.
"""
import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from app.services.repository import get_database_stats
from app.services.sync.delta import should_run_incremental_sync
from app.core.logging import app_logger


def render_global_status_alert(show_details: bool = False) -> None:
    """
    Renderiza alerta de status global dos dados.
    
    Args:
        show_details: Se deve mostrar detalhes por recurso
    """
    try:
        # Verificar status de todos os recursos
        resources = ['orders', 'equipments', 'technicians']
        status_info = check_global_status(resources)
        
        # Determinar tipo de alerta
        if status_info['critical_count'] > 0:
            render_critical_alert(status_info, show_details)
        elif status_info['warning_count'] > 0:
            render_warning_alert(status_info, show_details)
        elif status_info['total_records'] == 0:
            render_empty_db_alert()
        else:
            # Status OK - mostrar badge discreto
            if show_details:
                render_success_status(status_info)
    
    except Exception as e:
        st.error(f"❌ Erro ao verificar status: {e}")
        app_logger.log_error(f"Erro em render_global_status_alert: {e}")


def check_global_status(resources: List[str]) -> Dict:
    """Verifica status global de todos os recursos."""
    
    stats = get_database_stats()
    
    status_info = {
        'total_records': 0,
        'critical_count': 0,  # Nunca sincronizado
        'warning_count': 0,   # Desatualizado
        'ok_count': 0,        # Atualizado
        'resources': {},
        'last_global_sync': None
    }
    
    for resource in resources:
        count = stats.get(f'{resource}_count', 0)
        status_info['total_records'] += count
        
        # Verificar frescor
        is_fresh = not should_run_incremental_sync(resource, max_age_hours=2)
        
        # Classificar status
        if count == 0:
            status = 'critical'  # Nunca sincronizado
            status_info['critical_count'] += 1
        elif not is_fresh:
            status = 'warning'   # Desatualizado  
            status_info['warning_count'] += 1
        else:
            status = 'ok'        # Atualizado
            status_info['ok_count'] += 1
        
        status_info['resources'][resource] = {
            'count': count,
            'status': status,
            'is_fresh': is_fresh
        }
    
    # Encontrar última sincronização global
    last_syncs = stats.get('last_syncs', [])
    if last_syncs:
        status_info['last_global_sync'] = last_syncs[0].get('synced_at')
    
    return status_info


def render_critical_alert(status_info: Dict, show_details: bool) -> None:
    """Renderiza alerta crítico."""
    
    critical_count = status_info['critical_count']
    total_records = status_info['total_records']
    
    st.error(
        f"🚨 **Atenção**: {critical_count} tipo(s) de dados nunca foram sincronizados. "
        f"Total de registros: {total_records:,}"
    )
    
    if show_details:
        with st.expander("📋 Detalhes do Status"):
            render_detailed_status(status_info)
    
    # Botão de ação rápida
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Sincronizar Agora", type="primary"):
            trigger_emergency_sync(status_info)


def render_warning_alert(status_info: Dict, show_details: bool) -> None:
    """Renderiza alerta de aviso."""
    
    warning_count = status_info['warning_count']
    total_records = status_info['total_records']
    
    st.warning(
        f"⚠️ **Dados desatualizados**: {warning_count} tipo(s) de dados precisam ser atualizados. "
        f"Total de registros: {total_records:,}"
    )
    
    if show_details:
        with st.expander("📋 Detalhes do Status"):
            render_detailed_status(status_info)
    
    # Botão de ação suave
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Atualizar", type="secondary"):
            trigger_incremental_sync(status_info)


def render_empty_db_alert() -> None:
    """Renderiza alerta para banco vazio."""
    
    st.error(
        "📭 **Banco de dados vazio**: Nenhum dado foi sincronizado ainda. "
        "É necessário executar uma sincronização inicial."
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🚀 Primeira Sincronização", type="primary"):
            trigger_initial_sync()


def render_success_status(status_info: Dict) -> None:
    """Renderiza status de sucesso."""
    
    total_records = status_info['total_records']
    ok_count = status_info['ok_count']
    
    st.success(
        f"✅ **Dados atualizados**: {ok_count} tipo(s) de dados estão sincronizados. "
        f"Total de registros: {total_records:,}"
    )
    
    # Mostrar última sincronização
    last_sync = status_info.get('last_global_sync')
    if last_sync:
        try:
            dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
            formatted = dt.strftime("Última sincronização: %H:%M:%S - %d/%m/%Y")
            st.caption(formatted)
        except:
            st.caption(f"Última sincronização: {last_sync}")


def render_detailed_status(status_info: Dict) -> None:
    """Renderiza status detalhado por recurso."""
    
    resource_names = {
        'orders': '📋 Ordens de Serviço',
        'equipments': '🛠️ Equipamentos',
        'technicians': '👥 Técnicos'
    }
    
    for resource, details in status_info['resources'].items():
        name = resource_names.get(resource, resource.title())
        count = details['count']
        status = details['status']
        
        # Ícone e cor por status
        if status == 'critical':
            icon = "🔴"
            status_text = "Nunca sincronizado"
        elif status == 'warning':
            icon = "🟡"
            status_text = "Desatualizado"
        else:
            icon = "🟢"
            status_text = "Atualizado"
        
        st.markdown(f"{icon} **{name}**: {count:,} registros - *{status_text}*")


def trigger_emergency_sync(status_info: Dict) -> None:
    """Dispara sincronização de emergência."""
    
    st.info("🚨 Iniciando sincronização de emergência...")
    
    try:
        import asyncio
        from app.services.sync.ingest import BackfillSync
        
        # Identificar recursos que precisam de sync
        critical_resources = [
            resource for resource, details in status_info['resources'].items()
            if details['status'] == 'critical'
        ]
        
        # Executar backfill
        backfill = BackfillSync()
        asyncio.run(backfill.run_backfill(critical_resources, batch_size=50))
        
        st.success("✅ Sincronização de emergência concluída!")
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro na sincronização: {e}")


def trigger_incremental_sync(status_info: Dict) -> None:
    """Dispara sincronização incremental."""
    
    st.info("🔄 Iniciando sincronização incremental...")
    
    try:
        import asyncio
        from app.services.sync.delta import run_incremental_sync
        
        # Identificar recursos que precisam de atualização
        warning_resources = [
            resource for resource, details in status_info['resources'].items()
            if details['status'] == 'warning'
        ]
        
        # Criar cliente da API
        from app.arkmeds_client.client import ArkmedsClient
        from app.arkmeds_client.auth import ArkmedsAuth
        auth = ArkmedsAuth()
        client = ArkmedsClient(auth)
        
        # Executar sync incremental
        if warning_resources:
            asyncio.run(run_incremental_sync(client, warning_resources))
        
        st.success("✅ Sincronização incremental concluída!")
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro na sincronização: {e}")


def trigger_initial_sync() -> None:
    """Dispara sincronização inicial."""
    
    st.info("🚀 Iniciando primeira sincronização...")
    
    try:
        import asyncio
        from app.services.sync.ingest import BackfillSync
        
        backfill = BackfillSync()
        asyncio.run(backfill.run_backfill(['orders', 'equipments', 'technicians'], batch_size=100))
        
        st.success("✅ Primeira sincronização concluída!")
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Erro na sincronização inicial: {e}")


# ========== COMPONENTES AUXILIARES ==========

def render_status_banner() -> None:
    """Renderiza banner de status na parte superior."""
    
    try:
        status_info = check_global_status(['orders', 'equipments', 'technicians'])
        
        if status_info['critical_count'] > 0:
            st.markdown("""
                <div style="background-color: #ff4b4b; color: white; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    🚨 <strong>Atenção:</strong> Alguns dados nunca foram sincronizados. 
                    <a href="#sync" style="color: white; text-decoration: underline;">Sincronizar agora</a>
                </div>
            """, unsafe_allow_html=True)
        elif status_info['warning_count'] > 0:
            st.markdown("""
                <div style="background-color: #ffa500; color: white; padding: 10px; border-radius: 5px; margin: 10px 0;">
                    ⚠️ <strong>Dados desatualizados.</strong> 
                    <a href="#update" style="color: white; text-decoration: underline;">Atualizar</a>
                </div>
            """, unsafe_allow_html=True)
    
    except Exception:
        pass  # Falha silenciosa para não quebrar a página


def render_floating_status_indicator() -> None:
    """Renderiza indicador flutuante de status."""
    
    try:
        status_info = check_global_status(['orders', 'equipments', 'technicians'])
        
        # CSS para indicador flutuante
        if status_info['critical_count'] > 0:
            color = "#ff4b4b"
            icon = "🚨"
        elif status_info['warning_count'] > 0:
            color = "#ffa500"
            icon = "⚠️"
        else:
            color = "#00cc00"
            icon = "✅"
        
        st.markdown(f"""
            <div style="
                position: fixed; 
                top: 20px; 
                right: 20px; 
                background: {color}; 
                color: white; 
                padding: 10px; 
                border-radius: 50%; 
                z-index: 1000;
                font-size: 16px;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
            " title="Status da Sincronização">
                {icon}
            </div>
        """, unsafe_allow_html=True)
    
    except Exception:
        pass  # Falha silenciosa
