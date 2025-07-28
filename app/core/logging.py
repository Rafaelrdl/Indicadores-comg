"""Sistema de logging centralizado para a aplicação."""

from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, cast

import streamlit as st

# Import do novo sistema estruturado
from .structlog_system import (
    struct_logger,
    LogContext,
    setup_logging
)


class AppLogger:
    """Logger centralizado da aplicação - Compatibilidade com structlog."""
    
    _instance: Optional[AppLogger] = None
    
    def __new__(cls) -> AppLogger:
        if cls._instance is None:
            cls._instance = cast(AppLogger, super().__new__(cls))
        return cls._instance
    
    def __init__(self) -> None:
        # Usar o logger estruturado
        self._logger = struct_logger
    
    def log_performance(self, func_name: str, duration: float, **kwargs: Any) -> None:
        """Log de performance de função."""
        self._logger.log_performance(func_name, duration, **kwargs)
        
        # Opcional: mostrar no Streamlit se duração for alta
        if duration > 5.0:
            st.warning(f"⚠️ Operação demorada: {func_name} ({duration:.1f}s)")
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log de erros com contexto."""
        self._logger.log_error(error, context or {})
    
    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log de informações gerais."""
        self._logger.log_info(message, **kwargs)
    
    def log_cache_hit(self, func_name: str, cache_key: Optional[str] = None) -> None:
        """Log de cache hit."""
        self._logger.log_cache_hit(func_name, cache_key or "")
    
    def log_cache_miss(self, func_name: str, cache_key: Optional[str] = None) -> None:
        """Log de cache miss."""
        self._logger.log_cache_miss(func_name, cache_key or "")


def performance_monitor(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator para monitorar performance de funções."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        request_id = LogContext.generate_request_id()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            app_logger.log_performance(
                func.__name__, 
                duration,
                request_id=request_id,
                args_count=len(args),
                has_kwargs=bool(kwargs)
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            app_logger.log_error(
                e, 
                {
                    "function": func.__name__,
                    "duration": duration,
                    "request_id": request_id
                }
            )
            raise
    
    return wrapper


def log_cache_performance(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator para monitorar performance de cache."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Cache hit geralmente é muito rápido (< 0.01s)
        is_cache_hit = duration < 0.01
        
        if is_cache_hit:
            app_logger.log_cache_hit(func.__name__)
        else:
            app_logger.log_cache_miss(func.__name__)
        
        app_logger.log_performance(
            func.__name__, 
            duration,
            cache_status="hit" if is_cache_hit else "miss"
        )
        
        return result
    
    return wrapper


# Instância global do logger - compatibilidade
app_logger = AppLogger()

# Funções de inicialização
def initialize_logging() -> None:
    """Inicializa o sistema de logging estruturado."""
    setup_logging()
    app_logger.log_info("Logging system initialized", event="system_startup")
