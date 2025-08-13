"""Sistema de logging estruturado com structlog - F1 Compliant."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any

import streamlit as st
import structlog

from .config import get_settings


class StructLogConfig:
    """Configuração centralizada do structlog."""

    @staticmethod
    def configure_structlog() -> None:
        """Configura o structlog com processadores otimizados."""
        settings = get_settings()

        # Configurar processadores
        processors = [
            structlog.contextvars.merge_contextvars,  # Merge context variables
            structlog.processors.TimeStamper(fmt="ISO"),  # ISO timestamp
            structlog.processors.add_log_level,  # Add log level
            structlog.processors.StackInfoRenderer(),  # Stack info if available
        ]

        # Adicionar processador de desenvolvimento se necessário
        if settings.debug_mode:
            processors.append(structlog.dev.ConsoleRenderer())
        else:
            processors.append(structlog.processors.JSONRenderer())

        # Configurar structlog
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


class LogContext:
    """Gerenciador de contexto para logs estruturados."""

    @staticmethod
    def generate_request_id() -> str:
        """Gera um request_id único."""
        return str(uuid.uuid4())[:8]

    @staticmethod
    def get_org_id() -> str | None:
        """Obtém org_id do contexto da sessão."""
        # Por enquanto retorna default, será implementado quando tivermos multi-tenant
        return st.session_state.get("org_id", "default")

    @staticmethod
    def get_user_id() -> str | None:
        """Obtém user_id do contexto da sessão."""
        return st.session_state.get("user_id", "anonymous")

    @staticmethod
    def create_context(**extra: Any) -> dict[str, Any]:
        """Cria contexto padrão para logs."""
        return {
            "request_id": LogContext.generate_request_id(),
            "org_id": LogContext.get_org_id(),
            "user_id": LogContext.get_user_id(),
            "timestamp": datetime.now().isoformat(),
            **extra,
        }


class StructuredLogger:
    """Logger estruturado usando structlog - F1 Compliant."""

    _instance: StructuredLogger | None = None
    _logger: structlog.BoundLogger | None = None

    def __new__(cls) -> StructuredLogger:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_structured_logging()

    def _setup_structured_logging(self) -> None:
        """Configura o sistema de logging estruturado."""
        StructLogConfig.configure_structlog()
        self._logger = structlog.get_logger("indicadores_comg")

    def log_performance(
        self, func_name: str, duration: float, request_id: str | None = None, **kwargs
    ) -> None:
        """Log de performance de função com contexto estruturado."""
        context = LogContext.create_context(
            event="performance",
            function=func_name,
            duration_seconds=round(duration, 3),
            request_id=request_id or LogContext.generate_request_id(),
            **kwargs,
        )

        # Log level baseado na duração
        if duration > 5.0:
            self._logger.warning("Slow function execution", **context)
            # Mostrar aviso no Streamlit se duração for alta
            if duration > 10.0:
                st.warning(f"⚠️ Operação demorada: {func_name} ({duration:.1f}s)")
        else:
            self._logger.info("Function execution", **context)

    def log_error(
        self, error: Exception, context: dict[str, Any] | None = None, request_id: str | None = None
    ) -> None:
        """Log de erros com contexto estruturado."""
        error_context = LogContext.create_context(
            event="error",
            error_type=type(error).__name__,
            error_message=str(error),
            request_id=request_id or LogContext.generate_request_id(),
            **(context or {}),
        )

        self._logger.error("Application error", **error_context)

    def log_info(self, message: str, request_id: str | None = None, **kwargs) -> None:
        """Log de informações gerais."""
        context = LogContext.create_context(
            event="info",
            message=message,
            request_id=request_id or LogContext.generate_request_id(),
            **kwargs,
        )

        self._logger.info("Application info", **context)

    def log_cache_hit(
        self, func_name: str, cache_key: str | None = None, request_id: str | None = None
    ) -> None:
        """Log de cache hit."""
        context = LogContext.create_context(
            event="cache_hit",
            function=func_name,
            cache_key=cache_key,
            request_id=request_id or LogContext.generate_request_id(),
        )

        self._logger.info("Cache hit", **context)

    def log_cache_miss(
        self, func_name: str, cache_key: str | None = None, request_id: str | None = None
    ) -> None:
        """Log de cache miss."""
        context = LogContext.create_context(
            event="cache_miss",
            function=func_name,
            cache_key=cache_key,
            request_id=request_id or LogContext.generate_request_id(),
        )

        self._logger.info("Cache miss", **context)

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float,
        request_id: str | None = None,
        **kwargs,
    ) -> None:
        """Log de chamadas de API."""
        context = LogContext.create_context(
            event="api_call",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_seconds=round(duration, 3),
            request_id=request_id or LogContext.generate_request_id(),
            **kwargs,
        )

        if status_code >= 400:
            self._logger.warning("API call failed", **context)
        else:
            self._logger.info("API call success", **context)


def structured_performance_monitor(func: Callable) -> Callable:
    """Decorator para monitorar performance com logging estruturado."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = LogContext.generate_request_id()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            struct_logger.log_performance(
                func_name=func.__name__,
                duration=duration,
                request_id=request_id,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()) if kwargs else [],
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            struct_logger.log_error(
                error=e,
                context={
                    "function": func.__name__,
                    "duration": duration,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()) if kwargs else [],
                },
                request_id=request_id,
            )
            raise

    return wrapper


def structured_cache_performance(func: Callable) -> Callable:
    """Decorator para monitorar performance de cache com logging estruturado."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = LogContext.generate_request_id()

        # Detectar se é cache hit ou miss baseado no tempo de execução
        result = func(*args, **kwargs)
        duration = time.time() - start_time

        # Cache hit geralmente é muito rápido (< 0.01s)
        is_cache_hit = duration < 0.01

        if is_cache_hit:
            struct_logger.log_cache_hit(func_name=func.__name__, request_id=request_id)
        else:
            struct_logger.log_cache_miss(func_name=func.__name__, request_id=request_id)

        struct_logger.log_performance(
            func_name=func.__name__,
            duration=duration,
            request_id=request_id,
            cache_status="hit" if is_cache_hit else "miss",
        )

        return result

    return wrapper


# Instâncias globais - mantém compatibilidade
struct_logger = StructuredLogger()

# Alias para compatibilidade com código existente
app_logger = struct_logger

# Novos decorators recomendados
performance_monitor = structured_performance_monitor
log_cache_performance = structured_cache_performance


# Função de inicialização
def setup_logging() -> None:
    """Configura o sistema de logging estruturado."""
    StructLogConfig.configure_structlog()
    struct_logger.log_info("Structured logging initialized", event="system_startup")
