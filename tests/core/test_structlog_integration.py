"""Testes para integração do sistema de logging estruturado."""

import pytest
from unittest.mock import patch
import time

from app.core.logging import app_logger, performance_monitor, initialize_logging
from app.core.structlog_system import struct_logger, LogContext


class TestStructLogIntegration:
    """Testes de integração do sistema structlog."""

    def test_app_logger_initialization(self):
        """Testa se o AppLogger é um singleton."""
        from app.core.logging import AppLogger

        logger1 = AppLogger()
        logger2 = AppLogger()

        assert logger1 is logger2
        assert logger1 is app_logger

    def test_app_logger_performance_log(self):
        """Testa se o log de performance funciona."""
        # Teste básico - não deve gerar exceção
        app_logger.log_performance("test_function", 1.5, test_param="value")

    def test_app_logger_error_log(self):
        """Testa se o log de erro funciona."""
        test_error = ValueError("Test error")
        context = {"test_key": "test_value"}

        # Teste básico - não deve gerar exceção
        app_logger.log_error(test_error, context)

    def test_app_logger_info_log(self):
        """Testa se o log de info funciona."""
        # Teste básico - não deve gerar exceção
        app_logger.log_info("Test message", event="test")

    def test_app_logger_cache_logs(self):
        """Testa se os logs de cache funcionam."""
        # Teste básico - não deve gerar exceção
        app_logger.log_cache_hit("test_function", "test_key")
        app_logger.log_cache_miss("test_function", "test_key")
        app_logger.log_cache_hit("test_function")  # Sem cache_key
        app_logger.log_cache_miss("test_function")  # Sem cache_key

    def test_performance_monitor_decorator(self):
        """Testa se o decorator de performance funciona."""

        @performance_monitor
        def test_function(x: int, y: int = 10) -> int:
            time.sleep(0.01)  # Simular algum processamento
            return x + y

        result = test_function(5, y=15)
        assert result == 20

    def test_performance_monitor_with_error(self):
        """Testa se o decorator captura erros corretamente."""

        @performance_monitor
        def test_error_function():
            raise ValueError("Test error in decorated function")

        with pytest.raises(ValueError, match="Test error in decorated function"):
            test_error_function()

    def test_initialize_logging(self):
        """Testa se a inicialização do logging funciona."""
        # Teste básico - não deve gerar exceção
        initialize_logging()

    def test_log_context_request_id_generation(self):
        """Testa se a geração de request_id funciona."""
        request_id_1 = LogContext.generate_request_id()
        request_id_2 = LogContext.generate_request_id()

        assert request_id_1 != request_id_2
        assert len(request_id_1) == 8  # Tamanho definido no sistema
        assert len(request_id_2) == 8


@pytest.mark.asyncio
class TestStructLogWithStreamlit:
    """Testes específicos para integração com Streamlit."""

    @patch("streamlit.warning")
    def test_slow_function_warning(self, mock_warning):
        """Testa se operações lentas geram warning no Streamlit."""

        @performance_monitor
        def slow_function():
            time.sleep(0.01)  # Simular operação lenta
            return "done"

        # Mockar uma duração alta para testar o warning
        with patch("time.time", side_effect=[0, 6.0]):  # 6 segundos de duração
            result = slow_function()

        assert result == "done"
        # Verificar se o warning foi chamado para operações > 5s
        mock_warning.assert_called_once()
        warning_call = mock_warning.call_args[0][0]
        assert "⚠️ Operação demorada" in warning_call
        assert "slow_function" in warning_call
        assert "6.0s" in warning_call


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
