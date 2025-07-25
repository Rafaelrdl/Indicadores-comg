"""Testes unitários para o módulo core de exceções."""

import pytest
from unittest.mock import patch, MagicMock

from app.core.exceptions import (
    AppException,
    DataFetchError,
    DataProcessingError,
    AuthenticationError,
    ValidationError,
    ErrorHandler,
    safe_operation,
    validate_data,
    validate_not_empty
)


class TestAppException:
    """Testes para a exceção base AppException."""
    
    def test_app_exception_creation(self):
        """Testa criação de AppException."""
        context = {"key": "value"}
        exception = AppException("Test message", context)
        
        assert exception.message == "Test message"
        assert exception.context == context
        assert exception.timestamp is not None
        assert str(exception) == "Test message"
    
    def test_app_exception_without_context(self):
        """Testa criação de AppException sem contexto."""
        exception = AppException("Test message")
        
        assert exception.message == "Test message"
        assert exception.context == {}


class TestSpecificExceptions:
    """Testes para exceções específicas."""
    
    def test_data_fetch_error(self):
        """Testa DataFetchError."""
        error = DataFetchError("Fetch failed")
        assert isinstance(error, AppException)
        assert error.message == "Fetch failed"
    
    def test_data_processing_error(self):
        """Testa DataProcessingError."""
        error = DataProcessingError("Processing failed")
        assert isinstance(error, AppException)
        assert error.message == "Processing failed"
    
    def test_authentication_error(self):
        """Testa AuthenticationError."""
        error = AuthenticationError("Auth failed")
        assert isinstance(error, AppException)
        assert error.message == "Auth failed"
    
    def test_validation_error(self):
        """Testa ValidationError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, AppException)
        assert error.message == "Validation failed"


class TestErrorHandler:
    """Testes para a classe ErrorHandler."""
    
    @patch('streamlit.error')
    @patch('app.core.logging.app_logger')
    def test_handle_data_fetch_error(self, mock_logger, mock_st_error):
        """Testa manipulação de DataFetchError."""
        error = DataFetchError("API failed")
        ErrorHandler.handle_error(error)
        
        mock_logger.log_error.assert_called_once_with(error, None)
        mock_st_error.assert_called_once_with("❌ Erro ao carregar dados. Verifique sua conexão.")
    
    @patch('streamlit.error')
    @patch('app.core.logging.app_logger')
    def test_handle_authentication_error(self, mock_logger, mock_st_error):
        """Testa manipulação de AuthenticationError."""
        error = AuthenticationError("Login failed")
        ErrorHandler.handle_error(error)
        
        mock_logger.log_error.assert_called_once_with(error, None)
        mock_st_error.assert_called_once_with("🔐 Erro de autenticação. Verifique suas credenciais.")
    
    @patch('streamlit.error')
    @patch('app.core.logging.app_logger')
    def test_handle_custom_message(self, mock_logger, mock_st_error):
        """Testa manipulação com mensagem customizada."""
        error = Exception("Generic error")
        custom_message = "Custom error message"
        
        ErrorHandler.handle_error(error, user_message=custom_message)
        
        mock_logger.log_error.assert_called_once_with(error, None)
        mock_st_error.assert_called_once_with(custom_message)
    
    def test_safe_execute_success(self):
        """Testa execução segura com sucesso."""
        def test_func(x, y):
            return x + y
        
        result = ErrorHandler.safe_execute(test_func, 1, 2)
        assert result == 3
    
    @patch('app.core.exceptions.ErrorHandler.handle_error')
    def test_safe_execute_error(self, mock_handle_error):
        """Testa execução segura com erro."""
        def failing_func():
            raise ValueError("Test error")
        
        fallback = "fallback_value"
        result = ErrorHandler.safe_execute(failing_func, fallback_value=fallback)
        
        assert result == fallback
        mock_handle_error.assert_called_once()


class TestSafeOperation:
    """Testes para o decorator safe_operation."""
    
    def test_safe_operation_success(self):
        """Testa decorator com função que executa com sucesso."""
        
        @safe_operation(fallback_value="fallback")
        def test_function(x):
            return x * 2
        
        result = test_function(5)
        assert result == 10
    
    @patch('app.core.exceptions.ErrorHandler.handle_error')
    def test_safe_operation_error(self, mock_handle_error):
        """Testa decorator com função que falha."""
        
        @safe_operation(fallback_value="fallback")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        assert result == "fallback"
        mock_handle_error.assert_called_once()


class TestValidationFunctions:
    """Testes para funções de validação."""
    
    def test_validate_data_success(self):
        """Testa validação de dados com sucesso."""
        # Não deve gerar exceção
        validate_data("test", str, "test_field")
        validate_data(123, int, "number_field")
        validate_data([], list, "list_field")
    
    def test_validate_data_failure(self):
        """Testa validação de dados com falha."""
        with pytest.raises(ValidationError) as exc_info:
            validate_data("test", int, "number_field")
        
        assert "number_field deve ser do tipo int" in str(exc_info.value)
    
    def test_validate_not_empty_success(self):
        """Testa validação de não vazio com sucesso."""
        # Não deve gerar exceção
        validate_not_empty("test", "string_field")
        validate_not_empty([1, 2, 3], "list_field")
        validate_not_empty({"key": "value"}, "dict_field")
    
    def test_validate_not_empty_failure(self):
        """Testa validação de não vazio com falha."""
        test_cases = [
            ("", "empty_string"),
            ([], "empty_list"),
            ({}, "empty_dict"),
            (None, "none_value"),
            (0, "zero_value")
        ]
        
        for empty_value, field_name in test_cases:
            with pytest.raises(ValidationError) as exc_info:
                validate_not_empty(empty_value, field_name)
            
            assert f"{field_name} não pode estar vazio" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
