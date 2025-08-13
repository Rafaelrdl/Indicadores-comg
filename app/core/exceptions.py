"""Centralized exception handling system."""

from __future__ import annotations

from datetime import datetime
from typing import Any, TypeVar

import streamlit as st


T = TypeVar("T")


class AppException(Exception):
    """Base application exception with enhanced context tracking."""

    def __init__(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        original_error: Exception | None = None,
        error_code: str | None = None,
    ):
        self.message = message
        self.context = context or {}
        self.original_error = original_error
        self.error_code = error_code
        self.timestamp = datetime.now()
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "error_code": self.error_code,
            "timestamp": self.timestamp.isoformat(),
            "original_error": str(self.original_error) if self.original_error else None,
        }


class DataFetchError(AppException):
    """Error fetching data from external APIs."""

    pass


class DataProcessingError(AppException):
    """Error processing or transforming data."""

    pass


class AuthenticationError(AppException):
    """Authentication and authorization errors."""

    pass


class ValidationError(AppException):
    """Data validation errors."""

    pass


class CacheError(AppException):
    """Cache-related errors."""

    pass


class ConfigurationError(AppException):
    """Configuration and settings errors."""

    pass


class RateLimitError(AppException):
    """API rate limit exceeded."""

    pass


class TimeoutError(AppException):
    """Operation timeout errors."""

    pass


class APIError(AppException):
    """Error communicating with external APIs."""

    pass


# Legacy compatibility aliases
ApplicationError = AppException
DataValidationError = ValidationError


class ErrorHandler:
    """Manipulador centralizado de erros."""

    @staticmethod
    def handle_error(
        error: Exception,
        context: dict[str, Any] = None,
        show_user_message: bool = True,
        user_message: str = None,
    ) -> None:
        """Manipula erros de forma centralizada."""
        from app.core.logging import app_logger

        # Log do erro
        app_logger.log_error(error, context)

        # Mensagem para o usuário
        if show_user_message:
            if isinstance(error, DataFetchError):
                st.error("❌ Erro ao carregar dados. Verifique sua conexão.")
            elif isinstance(error, AuthenticationError):
                st.error("🔐 Erro de autenticação. Verifique suas credenciais.")
            elif isinstance(error, DataProcessingError):
                st.error("⚙️ Erro ao processar dados. Tente novamente.")
            elif isinstance(error, ValidationError):
                st.error(f"⚠️ Dados inválidos: {error.message}")
            elif user_message:
                st.error(user_message)
            else:
                st.error("❌ Ocorreu um erro inesperado. Tente novamente.")

    @staticmethod
    def safe_execute(
        func,
        *args,
        fallback_value: Any = None,
        error_message: str = None,
        show_error: bool = True,
        **kwargs,
    ) -> Any:
        """Executa função de forma segura com tratamento de erro."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_error(
                error=e,
                context={
                    "function": func.__name__ if hasattr(func, "__name__") else str(func),
                    "args": str(args)[:100],  # Limitar tamanho do log
                    "kwargs": str(kwargs)[:100],
                },
                show_user_message=show_error,
                user_message=error_message,
            )
            return fallback_value


def safe_operation(fallback_value: Any = None, error_message: str = None, show_error: bool = True):
    """Decorator para operações seguras."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            return ErrorHandler.safe_execute(
                func,
                *args,
                fallback_value=fallback_value,
                error_message=error_message,
                show_error=show_error,
                **kwargs,
            )

        return wrapper

    return decorator


def validate_data(data: Any, expected_type: type, field_name: str = "data") -> None:
    """Valida tipos de dados."""
    if not isinstance(data, expected_type):
        raise ValidationError(
            f"{field_name} deve ser do tipo {expected_type.__name__}, "
            f"recebido {type(data).__name__}",
            context={"expected_type": expected_type.__name__, "actual_type": type(data).__name__},
        )


def validate_not_empty(data: Any, field_name: str = "data") -> None:
    """Valida que dados não estão vazios."""
    if not data:
        raise ValidationError(
            f"{field_name} não pode estar vazio",
            context={"field_name": field_name, "data": str(data)[:50]},
        )
