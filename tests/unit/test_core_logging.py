"""Testes unitários para o módulo core de logging."""

import pytest
import time
from unittest.mock import patch, MagicMock

from app.core.logging import AppLogger, performance_monitor, log_cache_performance


class TestAppLogger:
    """Testes para a classe AppLogger."""

    def test_singleton_pattern(self):
        """Testa se AppLogger implementa corretamente o padrão Singleton."""
        logger1 = AppLogger()
        logger2 = AppLogger()
        assert logger1 is logger2

    def test_log_performance(self):
        """Testa o logging de performance."""
        logger = AppLogger()

        with patch.object(logger._logger, "info") as mock_info:
            logger.log_performance("test_function", 1.5, extra_param="test")

            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "PERFORMANCE" in call_args
            assert "test_function" in call_args
            assert "1.5" in call_args

    def test_log_error(self):
        """Testa o logging de erros."""
        logger = AppLogger()
        test_error = ValueError("Erro de teste")

        with patch.object(logger._logger, "error") as mock_error:
            logger.log_error(test_error, {"context": "test"})

            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "ERROR" in call_args
            assert "ValueError" in call_args


class TestPerformanceMonitor:
    """Testes para o decorator de monitoramento de performance."""

    def test_performance_monitor_success(self):
        """Testa o decorator em função que executa com sucesso."""

        @performance_monitor
        def test_function(x, y):
            time.sleep(0.1)  # Simula processamento
            return x + y

        with patch("app.core.logging.AppLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger_class.return_value = mock_logger

            result = test_function(1, 2)

            assert result == 3
            mock_logger.log_performance.assert_called_once()

            # Verifica os argumentos do log
            call_args = mock_logger.log_performance.call_args
            assert call_args[1]["func_name"] == "test_function"
            assert call_args[1]["duration"] > 0.1  # Deve ter demorado pelo menos 0.1s

    def test_performance_monitor_error(self):
        """Testa o decorator em função que gera erro."""

        @performance_monitor
        def failing_function():
            raise ValueError("Erro de teste")

        with patch("app.core.logging.AppLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger_class.return_value = mock_logger

            with pytest.raises(ValueError):
                failing_function()

            mock_logger.log_error.assert_called_once()


class TestCachePerformanceMonitor:
    """Testes para o decorator de monitoramento de cache."""

    def test_cache_hit_detection(self):
        """Testa detecção de cache hit (execução rápida)."""

        @log_cache_performance
        def fast_function():
            return "result"

        with patch("app.core.logging.AppLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger_class.return_value = mock_logger

            result = fast_function()

            assert result == "result"
            mock_logger.log_cache_hit.assert_called_once()

    def test_cache_miss_detection(self):
        """Testa detecção de cache miss (execução lenta)."""

        @log_cache_performance
        def slow_function():
            time.sleep(0.2)  # Força execução lenta
            return "result"

        with patch("app.core.logging.AppLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger_class.return_value = mock_logger

            result = slow_function()

            assert result == "result"
            mock_logger.log_cache_miss.assert_called_once()
            mock_logger.log_performance.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
