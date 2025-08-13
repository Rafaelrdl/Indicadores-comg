"""Testes para ArkmedsAuth usando respx para mocks HTTP.

Este módulo testa o sistema de autenticação da API Arkmeds,
incluindo descoberta de endpoints e tratamento de erros.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
import respx
import httpx

from app.arkmeds_client.auth import ArkmedsAuth, ArkmedsAuthError
from app.arkmeds_client.models import TokenData


class TestArkmedsAuth:
    """Testes para autenticação ArkmedsAuth."""

    @pytest.fixture
    def auth_config(self):
        """Configuração básica para testes."""
        return {
            "email": "test@example.com",
            "password": "testpass",
            "base_url": "https://api.test.com",
        }

    @pytest.fixture
    def mock_auth(self, auth_config):
        """Instância de ArkmedsAuth para testes."""
        return ArkmedsAuth(**auth_config)

    @respx.mock
    async def test_login_success_token_auth(self, mock_auth):
        """Testa login bem-sucedido com /rest-auth/token-auth/."""
        # Mock do endpoint de login
        respx.post("https://api.test.com/rest-auth/token-auth/").mock(
            return_value=httpx.Response(200, json={"token": "test_jwt_token_12345"})
        )

        # Executar login
        token_data = await mock_auth.login()

        # Verificações
        assert isinstance(token_data, TokenData)
        assert token_data.token == "test_jwt_token_12345"
        assert isinstance(token_data.exp, datetime)
        assert token_data.exp > datetime.now(timezone.utc)

    @respx.mock
    async def test_login_discovery_fallback(self, mock_auth):
        """Testa descoberta de endpoint quando o primeiro falha."""
        # Mock: primeiro endpoint retorna 404
        respx.post("https://api.test.com/rest-auth/token-auth/").mock(
            return_value=httpx.Response(404, text="Not found")
        )

        # Mock: segundo endpoint funciona
        respx.post("https://api.test.com/rest-auth/login/").mock(
            return_value=httpx.Response(200, json={"token": "fallback_token_67890"})
        )

        # Executar login
        token_data = await mock_auth.login()

        # Verificações
        assert token_data.token == "fallback_token_67890"
        assert mock_auth._login_url == "/rest-auth/login/"

    @respx.mock
    async def test_login_invalid_credentials(self, mock_auth):
        """Testa tratamento de credenciais inválidas."""
        # Mock: retorna 401 Unauthorized
        respx.post("https://api.test.com/rest-auth/token-auth/").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )

        # Verificar que levanta exceção apropriada
        with pytest.raises(ArkmedsAuthError, match="Invalid credentials"):
            await mock_auth.login()

    @respx.mock
    async def test_login_malformed_response(self, mock_auth):
        """Testa tratamento de resposta malformada."""
        # Mock: resposta sem token
        respx.post("https://api.test.com/rest-auth/token-auth/").mock(
            return_value=httpx.Response(200, json={"user": "test", "status": "ok"})  # Sem 'token'
        )

        # Verificar que levanta exceção apropriada
        with pytest.raises(ArkmedsAuthError, match="Malformed login response"):
            await mock_auth.login()

    @respx.mock
    async def test_discover_login_url_success(self, mock_auth):
        """Testa descoberta de URL de login."""
        # Mock: HEAD request retorna 200 para segundo endpoint
        respx.head("https://api.test.com/rest-auth/token-auth/").mock(
            return_value=httpx.Response(404)
        )
        respx.head("https://api.test.com/rest-auth/login/").mock(return_value=httpx.Response(200))

        # Executar descoberta
        login_url = await mock_auth._discover_login_url()

        # Verificação
        assert login_url == "/rest-auth/login/"
        assert mock_auth._login_url == "/rest-auth/login/"

    @respx.mock
    async def test_discover_login_url_not_found(self, mock_auth):
        """Testa falha na descoberta de URL de login."""
        # Mock: todos endpoints retornam 404
        for endpoint in ArkmedsAuth.LOGIN_ENDPOINT_CANDIDATES:
            respx.head(f"https://api.test.com{endpoint}").mock(return_value=httpx.Response(404))
            respx.request("OPTIONS", f"https://api.test.com{endpoint}").mock(
                return_value=httpx.Response(404)
            )

        # Verificar que levanta exceção apropriada
        with pytest.raises(ArkmedsAuthError, match="Login endpoint not found"):
            await mock_auth._discover_login_url()

    async def test_get_token_auto_login(self, mock_auth):
        """Testa que get_token() faz login automaticamente."""
        with patch.object(mock_auth, "login") as mock_login:
            # Configurar mock para retornar token
            future_exp = datetime.now(timezone.utc) + timedelta(hours=1)
            mock_token = TokenData(token="auto_login_token", exp=future_exp)
            mock_login.return_value = mock_token
            mock_auth._token = mock_token

            # Executar get_token
            token = await mock_auth.get_token()

            # Verificações
            assert token == "auto_login_token"
            mock_login.assert_called_once()

    async def test_refresh_near_expiry(self, mock_auth):
        """Testa refresh automático quando token próximo do vencimento."""
        # Configurar token que expira em 1 minuto
        near_exp = datetime.now(timezone.utc) + timedelta(minutes=1)
        mock_auth._token = TokenData(token="expiring_token", exp=near_exp)

        with patch.object(mock_auth, "login") as mock_login:
            # Configurar novo token
            future_exp = datetime.now(timezone.utc) + timedelta(hours=1)
            new_token = TokenData(token="refreshed_token", exp=future_exp)
            mock_login.return_value = new_token
            mock_auth._token = new_token

            # Executar refresh
            await mock_auth.refresh()

            # Verificar que login foi chamado
            mock_login.assert_called_once()

    async def test_refresh_valid_token(self, mock_auth):
        """Testa que tokens válidos não são renovados."""
        # Configurar token que expira em 1 hora
        future_exp = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_auth._token = TokenData(token="valid_token", exp=future_exp)

        with patch.object(mock_auth, "login") as mock_login:
            # Executar refresh
            await mock_auth.refresh()

            # Verificar que login NÃO foi chamado
            mock_login.assert_not_called()

    def test_invalid_base_url(self):
        """Testa validação de base_url."""
        with pytest.raises(ValueError, match="base_url must start with"):
            ArkmedsAuth(
                email="test@example.com",
                password="testpass",
                base_url="invalid-url",  # Sem protocolo
            )

    @patch("streamlit.secrets")
    def test_from_secrets(self, mock_secrets):
        """Testa criação a partir de secrets do Streamlit."""
        # Mock do streamlit.secrets
        mock_secrets.get.return_value = {
            "email": "secret@example.com",
            "password": "secretpass",
            "base_url": "https://secret.api.com",
            "token": "existing_token",
            "login_path": "/custom/login",
        }

        # Criar instância
        auth = ArkmedsAuth.from_secrets()

        # Verificações
        assert auth.email == "secret@example.com"
        assert auth.password == "secretpass"
        assert auth.base_url == "https://secret.api.com"
        assert auth._login_url == "/custom/login"
        assert auth._token is not None
        assert auth._token.token == "existing_token"


@pytest.mark.integration
class TestArkmedsAuthIntegration:
    """Testes de integração para ArkmedsAuth (requerem API real)."""

    @pytest.mark.api
    async def test_real_api_connection(self):
        """Teste de conexão com API real (pular se não configurado)."""
        pytest.skip("Teste de integração - configurar credenciais reais para executar")

        # Exemplo de teste de integração real:
        # auth = ArkmedsAuth.from_secrets()
        # token_data = await auth.login()
        # assert token_data.token
        # assert isinstance(token_data.exp, datetime)
