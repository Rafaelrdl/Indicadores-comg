"""
Sistema de agendamento automático para sincronização periódica.

Este módulo gerencia a execução automática de sincronizações incrementais
em intervalos regulares usando APScheduler em modo session-aware.
"""
import streamlit as st
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime
from typing import Optional
import asyncio
import threading

from app.services.sync.delta import run_incremental_sync
from app.core.logging import app_logger


class SyncScheduler:
    """
    Gerenciador de agendamento de sincronização automática.
    
    Usa BackgroundScheduler para executar sincronizações periódicas
    enquanto a sessão Streamlit estiver ativa.
    """
    
    def __init__(self, interval_minutes: int = 15):
        """
        Initialize scheduler with specified interval.
        
        Args:
            interval_minutes: Intervalo entre sincronizações em minutos
        """
        self.interval_minutes = interval_minutes
        self.scheduler: Optional[BackgroundScheduler] = None
        self.last_run: Optional[datetime] = None
        self.last_result: Optional[str] = None
        self._lock = threading.Lock()
        
    def start(self) -> None:
        """Inicia o scheduler."""
        if self.scheduler is not None and self.scheduler.running:
            app_logger.log_info(f"Scheduler já está rodando (intervalo: {self.interval_minutes}m)")
            return
            
        try:
            self.scheduler = BackgroundScheduler(
                daemon=True,
                timezone='America/Sao_Paulo'
            )
            
            # Adicionar job de sincronização
            self.scheduler.add_job(
                func=self._sync_wrapper,
                trigger="interval",
                minutes=self.interval_minutes,
                id="incremental_sync",
                name=f"Sync Incremental ({self.interval_minutes}m)",
                max_instances=1,  # Evita sobreposição
                coalesce=True     # Combina execuções atrasadas
            )
            
            # Adicionar listeners para logs
            self.scheduler.add_listener(
                self._job_executed_listener, 
                EVENT_JOB_EXECUTED
            )
            self.scheduler.add_listener(
                self._job_error_listener, 
                EVENT_JOB_ERROR
            )
            
            self.scheduler.start()
            app_logger.log_info(
                f"🕐 Scheduler iniciado - sincronização automática a cada {self.interval_minutes} minutos",
                scheduler_id="incremental_sync"
            )
            
        except Exception as e:
            app_logger.log_error(e, {"context": "scheduler_start"})
            raise
    
    def stop(self) -> None:
        """Para o scheduler."""
        if self.scheduler and self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=False)
                app_logger.log_info("🛑 Scheduler parado")
            except Exception as e:
                app_logger.log_error(e, {"context": "scheduler_stop"})
        
        self.scheduler = None
    
    def _sync_wrapper(self) -> None:
        """
        Wrapper para executar sincronização incremental de forma thread-safe.
        """
        with self._lock:
            try:
                app_logger.log_info("🔄 Iniciando sincronização automática agendada")
                
                # Executar sync incremental de forma assíncrona
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Executar sincronização
                result = loop.run_until_complete(run_incremental_sync())
                
                self.last_run = datetime.now()
                self.last_result = "sucesso" if result else "falha"
                
                app_logger.log_info(
                    f"✅ Sincronização automática concluída: {self.last_result}",
                    result=result,
                    timestamp=self.last_run.isoformat()
                )
                
            except Exception as e:
                self.last_run = datetime.now()
                self.last_result = f"erro: {str(e)}"
                app_logger.log_error(
                    e, 
                    {
                        "context": "scheduled_sync", 
                        "timestamp": self.last_run.isoformat()
                    }
                )
    
    def _job_executed_listener(self, event) -> None:
        """Listener para jobs executados com sucesso."""
        app_logger.log_info(
            f"📋 Job executado: {event.job_id}",
            duration_seconds=event.duration.total_seconds() if event.duration else 0,
            retval=str(event.retval) if event.retval else "None"
        )
    
    def _job_error_listener(self, event) -> None:
        """Listener para jobs com erro."""
        app_logger.log_error(
            event.exception,
            {
                "context": "scheduled_job_error",
                "job_id": event.job_id,
                "traceback": event.traceback
            }
        )
    
    def get_status(self) -> dict:
        """Retorna status atual do scheduler."""
        return {
            "running": self.scheduler is not None and self.scheduler.running,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run,
            "last_result": self.last_result,
            "next_run": self._get_next_run_time()
        }
    
    def _get_next_run_time(self) -> Optional[datetime]:
        """Retorna horário da próxima execução."""
        if not self.scheduler or not self.scheduler.running:
            return None
            
        try:
            job = self.scheduler.get_job("incremental_sync")
            return job.next_run_time if job else None
        except Exception:
            return None


@st.cache_resource
def get_scheduler() -> SyncScheduler:
    """
    Retorna instância singleton do scheduler com cache de resource.
    
    O cache_resource garante que o scheduler seja compartilhado entre
    sessões e mantido enquanto o app estiver ativo.
    """
    # Obter intervalo da configuração
    try:
        interval = int(st.secrets.get("SYNC_INTERVAL_MINUTES", 15))
    except Exception:
        # Fallback para variável de ambiente ou padrão
        import os
        interval = int(os.environ.get("SYNC_INTERVAL_MINUTES", 15))
    
    # Criar e iniciar scheduler
    scheduler = SyncScheduler(interval_minutes=interval)
    
    try:
        scheduler.start()
        app_logger.log_info(f"🚀 Sistema de agendamento inicializado (intervalo: {interval}m)")
    except Exception as e:
        app_logger.log_error(e, {"context": "scheduler_initialization"})
        # Retornar scheduler mesmo com erro - pode ser usado manualmente
    
    return scheduler


def initialize_scheduler() -> Optional[SyncScheduler]:
    """
    Inicializa o scheduler de forma segura.
    
    Returns:
        Instância do scheduler ou None se houver erro
    """
    try:
        scheduler = get_scheduler()
        app_logger.log_info("✅ Scheduler inicializado com sucesso")
        return scheduler
    except Exception as e:
        app_logger.log_error(e, {"context": "scheduler_init_safe"})
        return None


def get_scheduler_status() -> dict:
    """
    Retorna status do scheduler de forma segura.
    
    Returns:
        Dict com informações de status
    """
    try:
        scheduler = get_scheduler()
        return scheduler.get_status()
    except Exception as e:
        app_logger.log_error(e, {"context": "get_scheduler_status"})
        return {
            "running": False,
            "error": str(e),
            "interval_minutes": None,
            "last_run": None,
            "last_result": None,
            "next_run": None
        }
