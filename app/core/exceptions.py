"""Sistema centralizado de tratamento de exceções."""

from typing import Any, Dict, Optional, Type
import streamlit as st
from datetime import datetime


class AppException(Exception):
    """Exceção base da aplicação."""
    
    def __init__(self, message: str, context: Dict[str, Any] = None):
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)


class DataFetchError(AppException):
    """Erro ao buscar dados da API."""
    pass


class DataProcessingError(AppException):
    """Erro ao processar dados."""
    pass


class AuthenticationError(AppException):
    """Erro de autenticação."""
    pass


class ValidationError(AppException):
    """Erro de validação de dados."""
    pass


class ErrorHandler:
    """Manipulador centralizado de erros."""
    
    @staticmethod
    def handle_error(
        error: Exception,
        context: Dict[str, Any] = None,
        show_user_message: bool = True,
        user_message: str = None
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
        **kwargs
    ) -> Any:
        """Executa função de forma segura com tratamento de erro."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ErrorHandler.handle_error(
                error=e,
                context={
                    "function": func.__name__ if hasattr(func, '__name__') else str(func),
                    "args": str(args)[:100],  # Limitar tamanho do log
                    "kwargs": str(kwargs)[:100]
                },
                show_user_message=show_error,
                user_message=error_message
            )
            return fallback_value


def safe_operation(
    fallback_value: Any = None,
    error_message: str = None,
    show_error: bool = True
):
    """Decorator para operações seguras."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return ErrorHandler.safe_execute(
                func,
                *args,
                fallback_value=fallback_value,
                error_message=error_message,
                show_error=show_error,
                **kwargs
            )
        return wrapper
    return decorator


def validate_data(data: Any, expected_type: Type, field_name: str = "data") -> None:
    """Valida tipos de dados."""
    if not isinstance(data, expected_type):
        raise ValidationError(
            f"{field_name} deve ser do tipo {expected_type.__name__}, "
            f"recebido {type(data).__name__}",
            context={"expected_type": expected_type.__name__, "actual_type": type(data).__name__}
        )


def validate_not_empty(data: Any, field_name: str = "data") -> None:
    """Valida que dados não estão vazios."""
    if not data:
        raise ValidationError(
            f"{field_name} não pode estar vazio",
            context={"field_name": field_name, "data": str(data)[:50]}
        )
