"""Testes para ArkmedsClient usando respx para mocks HTTP.

Este módulo testa o cliente HTTP da API Arkmeds,
incluindo paginação, retry logic e tratamento de erros.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta

import pytest
import httpx

from app.arkmeds_client.client import ArkmedsClient
from app.arkmeds_client.auth import ArkmedsAuth, ArkmedsAuthError
from app.arkmeds_client.models import Equipment, Chamado, ResponsavelTecnico, Company


class TestArkmedsClient:
    """Testes para ArkmedsClient."""

    @pytest.fixture
    def mock_auth(self):
        """Mock de ArkmedsAuth para testes."""
        auth = AsyncMock(spec=ArkmedsAuth)
        auth.base_url = "https://api.test.com"
        auth.get_token.return_value = "test_token_12345"
        return auth

    @pytest.fixture
    def client(self, mock_auth):
        """Instância de ArkmedsClient para testes."""
        return ArkmedsClient(mock_auth, timeout=15.0, max_retries=3)

    async def test_client_initialization(self, mock_auth):
        """Testa inicialização do cliente."""
        client = ArkmedsClient(mock_auth, timeout=15.0, max_retries=3)
        
        assert client.auth == mock_auth
        assert client.timeout == 15.0
        assert client.max_retries == 3
        assert client._client is None

    async def test_get_client_creates_httpx_client(self, client, mock_auth):
        """Testa criação do httpx.AsyncClient."""
        # Executar _get_client
        http_client = await client._get_client()
        
        # Verificações
        assert isinstance(http_client, httpx.AsyncClient)
        assert http_client.base_url == "https://api.test.com"
        assert "Authorization" in http_client.headers
        assert http_client.headers["Authorization"] == "JWT test_token_12345"
        mock_auth.get_token.assert_called_once()

    async def test_request_success(self, client):
        """Testa requisição HTTP bem-sucedida."""
        with patch.object(client, '_get_client') as mock_get_client:
            # Mock do cliente HTTP
            mock_http_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_http_client.request.return_value = mock_response
            mock_get_client.return_value = mock_http_client

            # Executar requisição
            response = await client._request("GET", "/test/endpoint")

            # Verificações
            assert response == mock_response
            mock_http_client.request.assert_called_once_with(
                "GET", "/test/endpoint", params=None
            )

    async def test_request_retry_on_401(self, client, mock_auth):
        """Testa retry automático em caso de 401 Unauthorized."""
        with patch.object(client, '_get_client') as mock_get_client:
            # Mock do cliente HTTP
            mock_http_client = AsyncMock()
            mock_get_client.return_value = mock_http_client
            
            # Primeira chamada retorna 401, segunda retorna 200
            response_401 = AsyncMock()
            response_401.status_code = 401
            response_200 = AsyncMock()
            response_200.status_code = 200
            response_200.raise_for_status.return_value = None
            
            mock_http_client.request.side_effect = [response_401, response_200]

            # Executar requisição
            response = await client._request("GET", "/test/endpoint")

            # Verificações
            assert response == response_200
            assert mock_http_client.request.call_count == 2
            mock_auth.login.assert_called_once()

    async def test_request_retry_on_500(self, client):
        """Testa retry automático em caso de erro 500."""
        with patch.object(client, '_get_client') as mock_get_client:
            with patch('asyncio.sleep') as mock_sleep:
                # Mock do cliente HTTP
                mock_http_client = AsyncMock()
                mock_get_client.return_value = mock_http_client
                
                # Primeira chamada retorna 500, segunda retorna 200
                response_500 = AsyncMock()
                response_500.status_code = 500
                response_200 = AsyncMock()
                response_200.status_code = 200
                response_200.raise_for_status.return_value = None
                
                mock_http_client.request.side_effect = [response_500, response_200]

                # Executar requisição
                response = await client._request("GET", "/test/endpoint")

                # Verificações
                assert response == response_200
                assert mock_http_client.request.call_count == 2
                mock_sleep.assert_called_once_with(1)  # 2^0 = 1

    async def test_request_max_retries_exceeded(self, client):
        """Testa falha após esgotar tentativas."""
        with patch.object(client, '_get_client') as mock_get_client:
            with patch('asyncio.sleep'):
                # Mock do cliente HTTP
                mock_http_client = AsyncMock()
                mock_get_client.return_value = mock_http_client
                
                # Todas as tentativas retornam 500
                response_500 = AsyncMock()
                response_500.status_code = 500
                response_500.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Server Error", request=AsyncMock(), response=response_500
                )
                mock_http_client.request.return_value = response_500

                # Verificar que levanta exceção após max_retries
                with pytest.raises(httpx.HTTPStatusError):
                    await client._request("GET", "/test/endpoint")

                # Verificar tentativas
                assert mock_http_client.request.call_count == 3  # max_retries

    async def test_list_chamados_success(self, client):
        """Testa listagem de chamados bem-sucedida."""
        with patch.object(client, '_get_client') as mock_get_client:
            # Mock do cliente HTTP
            mock_http_client = AsyncMock()
            mock_get_client.return_value = mock_http_client
            
            # Mock da resposta
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "results": [
                    {
                        "id": 1,
                        "chamados": 12345,
                        "chamado_arquivado": False,
                        "responsavel_id": 1,
                        "tempo": ["finalizado sem atraso", "normal", 1, 0],
                        "tempo_fechamento": ["vazio", "normal", 0, 0],
                        "get_resp_tecnico": {
                            "id": "1",
                            "nome": "João Silva",
                            "email": "joao@teste.com",
                            "has_avatar": False,
                            "has_resp_tecnico": True,
                            "avatar": "JS"
                        },
                        "ordem_servico": {
                            "numero": "OS-2024-001",
                            "data_criacao": "2024-07-01",
                            "equipamento": 123,
                            "tipo_servico": 1,
                            "estado": 2,
                            "prioridade": 2
                        }
                    }
                ]
            }
            mock_http_client.get.return_value = mock_response

            # Executar listagem
            chamados = await client.list_chamados({"page": 1, "page_size": 1})

            # Verificações
            assert len(chamados) == 1
            assert isinstance(chamados[0], Chamado)
            assert chamados[0].id == 1
            assert chamados[0].chamados == 12345
            assert chamados[0].responsavel_nome == "João Silva"
            assert chamados[0].numero_os == "OS-2024-001"

    async def test_list_equipment_success(self, client):
        """Testa listagem de equipamentos bem-sucedida."""
        with patch.object(client, '_get_all_pages') as mock_get_pages:
            # Mock dos dados retornados
            mock_get_pages.return_value = [
                {
                    "id": 1,
                    "equipamentos": [
                        {
                            "id": 101,
                            "fabricante": "Philips",
                            "modelo": "MX400",
                            "patrimonio": "PAT001",
                            "numero_serie": "SN123456",
                            "identificacao": "Monitor Cardíaco Sala 1",
                            "tipo": 1,
                            "tipo_criticidade": 3,
                            "prioridade": 2
                        }
                    ]
                }
            ]

            # Executar listagem
            equipments = await client.list_equipment()

            # Verificações
            assert len(equipments) == 1
            assert isinstance(equipments[0], Equipment)
            assert equipments[0].id == 101
            assert equipments[0].fabricante == "Philips"
            assert equipments[0].modelo == "MX400"
            assert equipments[0].display_name == "Monitor Cardíaco Sala 1"
            assert equipments[0].proprietario == 1  # ID da empresa

    async def test_list_tipos_fallback(self, client):
        """Testa fallback para tipos quando API não está disponível."""
        with patch.object(client, '_get_all_pages') as mock_get_pages:
            # Mock de erro 404
            mock_get_pages.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=AsyncMock(),
                response=AsyncMock(status_code=404)
            )

            # Executar listagem
            tipos = await client.list_tipos()

            # Verificações - deve retornar dados padrão
            assert len(tipos) == 4
            assert tipos[0]["id"] == 1
            assert tipos[0]["descricao"] == "Manutenção Preventiva"
            assert tipos[3]["id"] == 28
            assert tipos[3]["descricao"] == "Busca Ativa"

    async def test_list_estados_fallback(self, client):
        """Testa fallback para estados quando API não está disponível."""
        with patch.object(client, '_get_all_pages') as mock_get_pages:
            # Mock de erro de conexão
            mock_get_pages.side_effect = httpx.RequestError("Connection failed")

            # Executar listagem
            estados = await client.list_estados()

            # Verificações - deve retornar dados padrão
            assert len(estados) == 3
            assert estados[0]["id"] == 1
            assert estados[0]["descricao"] == "Aberta"
            assert estados[2]["id"] == 3
            assert estados[2]["descricao"] == "Cancelada"

    async def test_close_client(self, client):
        """Testa fechamento do cliente HTTP."""
        with patch.object(client, '_get_client') as mock_get_client:
            # Mock do cliente HTTP
            mock_http_client = AsyncMock()
            mock_get_client.return_value = mock_http_client
            client._client = mock_http_client

            # Executar fechamento
            await client.close()

            # Verificações
            mock_http_client.aclose.assert_called_once()
            assert client._client is None

    async def test_close_client_error_handling(self, client):
        """Testa tratamento de erros ao fechar cliente."""
        with patch.object(client, '_get_client') as mock_get_client:
            # Mock do cliente HTTP que falha ao fechar
            mock_http_client = AsyncMock()
            mock_http_client.aclose.side_effect = RuntimeError("Closed event loop")
            mock_get_client.return_value = mock_http_client
            client._client = mock_http_client

            # Executar fechamento - não deve levantar exceção
            await client.close()

            # Verificações
            assert client._client is None

    @patch('streamlit.session_state', {})
    def test_from_session_creates_new_client(self):
        """Testa criação de cliente a partir da sessão."""
        with patch('app.arkmeds_client.auth.ArkmedsAuth.from_secrets') as mock_from_secrets:
            mock_auth = AsyncMock(spec=ArkmedsAuth)
            mock_from_secrets.return_value = mock_auth

            # Executar from_session
            client = ArkmedsClient.from_session()

            # Verificações
            assert isinstance(client, ArkmedsClient)
            assert client.auth == mock_auth
            mock_from_secrets.assert_called_once()

    @patch('streamlit.session_state', {'_arkmeds_client': 'existing_client'})
    def test_from_session_returns_existing_client(self):
        """Testa retorno de cliente existente da sessão."""
        # Criar cliente existente na sessão
        existing_client = ArkmedsClient(AsyncMock())
        
        with patch('streamlit.session_state', {'_arkmeds_client': existing_client}):
            # Executar from_session
            client = ArkmedsClient.from_session()

            # Verificações
            assert client is existing_client


@pytest.mark.integration
class TestArkmedsClientIntegration:
    """Testes de integração para ArkmedsClient (requerem API real)."""

    @pytest.mark.api
    async def test_real_api_endpoints(self):
        """Teste de endpoints reais da API (pular se não configurado)."""
        pytest.skip("Teste de integração - configurar credenciais reais para executar")
        
        # Exemplo de teste de integração real:
        # client = ArkmedsClient.from_session()
        # chamados = await client.list_chamados({"page": 1, "page_size": 5})
        # assert len(chamados) >= 0
        # await client.close()
