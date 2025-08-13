"""Sistema de logging centralizado para a aplicação."""

import logging
import time
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, Optional


class AppLogger:
    """Logger centralizado da aplicação."""

    _instance: Optional["AppLogger"] = None
    _logger: logging.Logger | None = None

    def __new__(cls) -> "AppLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logging()

    def _setup_logging(self) -> None:
        """Configura o sistema de logging."""
        self._logger = logging.getLogger("indicadores_comg")
        self._logger.setLevel(logging.INFO)

        # Evita logs duplicados
        if not self._logger.handlers:
            # Handler para console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Formatter
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)

            self._logger.addHandler(console_handler)

    def log_performance(self, func_name: str, duration: float, **kwargs) -> None:
        """Log de performance de função."""
        context = {
            "function": func_name,
            "duration_seconds": round(duration, 3),
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }

        self._logger.info(f"PERFORMANCE: {func_name} executed in {duration:.3f}s - {context}")

        # Opcional: mostrar no Streamlit se duração for alta - mas só no thread principal
        try:
            import streamlit as st
            from streamlit.runtime.scriptrunner import get_script_run_ctx

            # Só mostrar warning se estivermos no contexto do Streamlit
            if get_script_run_ctx() is not None and duration > 5.0:
                st.warning(f"⚠️ Operação lenta detectada: {func_name} ({duration:.1f}s)")
        except Exception:
            # Ignore context errors - we're likely in a thread
            pass

    def log_error(self, error: Exception, context: dict[str, Any] = None) -> None:
        """Log de erros com contexto."""
        context = context or {}
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            **context,
        }

        self._logger.error(f"ERROR: {error_context}")

    def log_info(self, message: str, **kwargs) -> None:
        """Log de informações gerais."""
        context = {"timestamp": datetime.now().isoformat(), **kwargs}

        self._logger.info(f"INFO: {message} - {context}")

    def log_warning(self, message: str, **kwargs) -> None:
        """Log de warnings/avisos."""
        context = {"timestamp": datetime.now().isoformat(), **kwargs}

        self._logger.warning(f"WARNING: {message} - {context}")

    def log_cache_hit(self, func_name: str, cache_key: str = None) -> None:
        """Log de cache hit."""
        self._logger.info(f"CACHE HIT: {func_name} - key: {cache_key}")

    def log_cache_miss(self, func_name: str, cache_key: str = None) -> None:
        """Log de cache miss."""
        self._logger.info(f"CACHE MISS: {func_name} - key: {cache_key}")


def performance_monitor(func: Callable) -> Callable:
    """Decorator para monitorar performance de funções - thread safe."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = AppLogger()
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # Log da performance
            logger.log_performance(
                func_name=func.__name__,
                duration=duration,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.log_error(
                error=e,
                context={
                    "function": func.__name__,
                    "duration_before_error": duration,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                },
            )
            raise

    return wrapper


def log_cache_performance(func: Callable) -> Callable:
    """Decorator para monitorar performance de cache - thread safe."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = AppLogger()
        func_name = func.__name__

        # Simular verificação de cache (Streamlit cache não expõe isso diretamente)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # Se executou muito rápido, provavelmente foi cache hit
            if duration < 0.1:  # Menos de 100ms
                logger.log_cache_hit(func_name)
            else:
                logger.log_cache_miss(func_name)
                logger.log_performance(func_name, duration)

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.log_error(
                error=e,
                context={
                    "function": func_name,
                    "duration_before_error": duration,
                    "cache_operation": True,
                },
            )
            raise

    return wrapper


# Instância global do logger
app_logger = AppLogger()
