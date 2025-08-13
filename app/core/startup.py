"""
Sistema de sincronização automática na inicialização do app.

Este módulo garante que uma sincronização incremental seja executada
automaticamente quando o app é iniciado, sem duplicações ou bloqueios.
"""
import asyncio
import threading
from datetime import datetime, timedelta

import streamlit as st

from app.arkmeds_client.auth import ArkmedsAuth
from app.arkmeds_client.client import ArkmedsClient
from app.core.config import get_settings
from app.core.logging import app_logger
from app.services.sync.delta import run_delta_sync_with_progress
from app.services.sync_jobs import get_last_success_job, has_running_job


@st.cache_resource
def ensure_startup_sync() -> bool:
    """
    Garante que uma sincronização startup seja executada uma única vez por processo.
    
    Esta função é cached pelo Streamlit para executar apenas uma vez por
    instância do servidor, evitando duplicações quando múltiplas sessões
    são abertas.
    
    Returns:
        bool: True se sincronização foi iniciada, False se foi pulada
    """
    try:
        app_logger.log_info("🚀 Verificando necessidade de sincronização de startup...")

        # Verificar se há job rodando
        if has_running_job():
            app_logger.log_info("⏸️ Job já em execução, pulando startup sync")
            return False

        # Verificar se há uma sync recente (últimos 30 minutos)
        last_success = get_last_success_job()
        if last_success and _is_recent_sync(last_success):
            app_logger.log_info("✅ Sincronização recente encontrada, pulando startup sync")
            return False

        # Verificar credenciais
        settings = get_settings()
        if not settings.arkmeds_email or not settings.arkmeds_password:
            app_logger.log_info("⚠️ Credenciais não configuradas, pulando startup sync")
            return False

        # Iniciar sincronização em thread separada
        app_logger.log_info("🎯 Iniciando sincronização de startup em background...")
        thread = threading.Thread(
            target=_run_startup_sync_thread,
            daemon=True,
            name="StartupSync"
        )
        thread.start()

        return True

    except Exception as e:
        app_logger.log_error(e, {"context": "ensure_startup_sync"})
        return False


def _is_recent_sync(last_job: dict, max_minutes: int = 30) -> bool:
    """
    Verifica se o último job foi recente o suficiente.
    
    Args:
        last_job: Dict com dados do último job
        max_minutes: Máximo de minutos para considerar "recente"
        
    Returns:
        bool: True se o job é recente
    """
    try:
        if not last_job.get('finished_at'):
            return False

        finished_at = datetime.fromisoformat(last_job['finished_at'])
        max_age = timedelta(minutes=max_minutes)

        return datetime.now() - finished_at < max_age

    except Exception as e:
        app_logger.log_error(e, {"context": "_is_recent_sync"})
        return False


def _run_startup_sync_thread() -> None:
    """
    Executa sincronização em thread separada com gerenciamento de event loop.
    
    Esta função roda em background para não bloquear a inicialização do app.
    """
    try:
        app_logger.log_info("🔄 Thread de startup sync iniciada...")

        # Criar novo event loop para esta thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Criar cliente da API
            settings = get_settings()
            auth = ArkmedsAuth(
                email=settings.arkmeds_email,
                password=settings.arkmeds_password,
                base_url=settings.arkmeds_base_url,
                token=settings.arkmeds_token
            )
            client = ArkmedsClient(auth)

            # Executar sincronização
            total = loop.run_until_complete(
                run_delta_sync_with_progress(client, ['orders'])
            )

            app_logger.log_info(f"✅ Startup sync concluída: {total:,} registros")

        finally:
            loop.close()

    except Exception as e:
        app_logger.log_error(e, {"context": "_run_startup_sync_thread"})


def force_startup_sync() -> bool:
    """
    Força uma nova sincronização de startup, ignorando cache.
    
    Útil para testes ou quando se quer forçar uma nova sincronização.
    
    Returns:
        bool: True se sincronização foi iniciada
    """
    try:
        # Limpar cache para forçar nova execução
        ensure_startup_sync.clear()

        # Executar nova sincronização
        return ensure_startup_sync()

    except Exception as e:
        app_logger.log_error(e, {"context": "force_startup_sync"})
        return False


def get_startup_sync_status() -> dict:
    """
    Obtém informações sobre o status da sincronização de startup.
    
    Returns:
        dict: Status da sincronização (running job ou último sucesso)
    """
    try:
        # Verificar se há job rodando
        running = has_running_job()
        if running:
            return {
                'status': 'running',
                'job': running,
                'message': 'Sincronização em andamento...'
            }

        # Verificar último job bem-sucedido
        last_success = get_last_success_job()
        if last_success:
            return {
                'status': 'completed',
                'job': last_success,
                'message': f"Última sincronização: {last_success.get('finished_at', 'N/A')}"
            }

        return {
            'status': 'none',
            'job': None,
            'message': 'Nenhuma sincronização encontrada'
        }

    except Exception as e:
        app_logger.log_error(e, {"context": "get_startup_sync_status"})
        return {
            'status': 'error',
            'job': None,
            'message': f'Erro ao verificar status: {e!s}'
        }
