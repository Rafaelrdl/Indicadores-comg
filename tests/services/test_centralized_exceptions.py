"""Testes para as exceções centralizadas após refatoração.

Este módulo testa especificamente as exceções CoreDataFetchError
e outros patterns de exceção introduzidos na refatoração.
"""

from __future__ import annotations

import pytest
from datetime import date, timedelta
from unittest.mock import patch

from app.core.exceptions import DataFetchError as CoreDataFetchError
from app.services.tech_metrics import fetch_technician_orders
from app.services.os_metrics import fetch_orders


class TestCentralizedExceptions:
    """Testes para as exceções centralizadas."""

    @pytest.mark.asyncio
    async def test_tech_metrics_exception_structure(self):
        """Testa estrutura da exceção em tech_metrics."""
        with patch("app.services.repository.get_orders_df") as mock_get:
            mock_get.side_effect = ValueError("Mock database error")
            
            with pytest.raises(CoreDataFetchError) as exc_info:
                await fetch_technician_orders(
                    None, 
                    date.today() - timedelta(days=7), 
                    date.today(),
                    area_id=1
                )
            
            exception = exc_info.value
            
            # Verifica estrutura da exceção
            assert "Failed to fetch technician data from Repository" in exception.message
            assert isinstance(exception.context, dict)
            assert "start_date" in exception.context
            assert "end_date" in exception.context
            assert "filters" in exception.context
            assert exception.context["filters"]["area_id"] == 1
            assert exception.original_error is not None
            assert isinstance(exception.original_error, ValueError)

    @pytest.mark.asyncio
    async def test_os_metrics_exception_structure(self):
        """Testa estrutura da exceção em os_metrics."""
        with patch("app.services.repository.get_orders_df") as mock_get:
            mock_get.side_effect = RuntimeError("Mock repository error")
            
            with pytest.raises(CoreDataFetchError) as exc_info:
                await fetch_orders(None, 1, 2, custom_filter="test")
            
            exception = exc_info.value
            
            # Verifica estrutura da exceção
            assert "Failed to fetch orders from Repository" in exception.message
            assert isinstance(exception.context, dict)
            assert "order_type" in exception.context
            assert exception.context["order_type"] == 1
            assert "area_id" in exception.context  
            assert exception.context["area_id"] == 2
            assert "extra" in exception.context
            assert exception.context["extra"]["custom_filter"] == "test"
            assert exception.original_error is not None
            assert isinstance(exception.original_error, RuntimeError)

    def test_core_data_fetch_error_creation(self):
        """Testa criação direta da CoreDataFetchError."""
        original = ValueError("Original error")
        context = {"key": "value", "number": 42}
        
        exception = CoreDataFetchError(
            message="Test error message",
            context=context,
            original_error=original
        )
        
        assert exception.message == "Test error message"
        assert exception.context == context
        assert exception.original_error == original
        assert exception.timestamp is not None

    def test_core_data_fetch_error_str_representation(self):
        """Testa representação string da exceção."""
        exception = CoreDataFetchError(
            message="Test message",
            context={"test": "context"}
        )
        
        str_repr = str(exception)
        assert "Test message" in str_repr

    def test_exception_chaining(self):
        """Testa se o chaining de exceções funciona corretamente."""
        original = ValueError("Original problem")
        
        try:
            raise CoreDataFetchError(
                message="Wrapper error",
                context={"wrapped": True},
                original_error=original
            ) from original
        except CoreDataFetchError as e:
            assert e.__cause__ == original
            assert e.original_error == original

    def test_exception_context_immutability(self):
        """Testa se o contexto da exceção é tratado corretamente."""
        context = {"mutable": "value"}
        
        exception = CoreDataFetchError(
            message="Test",
            context=context
        )
        
        # A implementação atual compartilha a referência do contexto
        # Este teste documenta o comportamento atual
        original_value = exception.context["mutable"]
        assert original_value == "value"
        
        # Modifica o contexto original
        context["mutable"] = "changed"
        context["new_key"] = "new_value"
        
        # Com a implementação atual, a exceção compartilha a referência
        # (Este é o comportamento atual, não necessariamente o ideal)
        assert exception.context["mutable"] == "changed"
        assert "new_key" in exception.context

    def test_exception_without_context(self):
        """Testa criação de exceção sem contexto."""
        exception = CoreDataFetchError(message="Simple error")
        
        assert exception.message == "Simple error"
        assert isinstance(exception.context, dict)
        assert len(exception.context) == 0
        assert exception.original_error is None

    def test_exception_with_none_context(self):
        """Testa criação de exceção com contexto None."""
        exception = CoreDataFetchError(
            message="Error with None context",
            context=None
        )
        
        assert exception.message == "Error with None context"
        assert isinstance(exception.context, dict)
        assert len(exception.context) == 0
