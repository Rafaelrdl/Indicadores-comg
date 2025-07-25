from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
import     async def list_os(self, **filters: Any) -> List[Chamado]:
        """
        Lista ordens de serviço (agora usando endpoint de chamados).
        
        MIGRAÇÃO: Este método agora retorna dados de Chamado que 
        contêm informações mais ricas incluindo dados da OS associada.
        """
        # Converter filtros antigos para o novo formato
        filters_dict = dict(filters) if filters else {}
        return await self.list_chamados(filters_dict)eamlit as st

from .auth import ArkmedsAuth, ArkmedsAuthError
from .models import (
    Equipment,
    OSEstado,
    PaginatedResponse,
    TipoOS,
    Chamado,
    ResponsavelTecnico,
)


class ArkmedsClient:
    @classmethod
    def from_session(cls) -> "ArkmedsClient":
        client = st.session_state.get("_arkmeds_client")
        if isinstance(client, cls):
            return client
        auth = ArkmedsAuth.from_secrets()
        client = cls(auth)
        st.session_state["_arkmeds_client"] = client
        return client

    def __init__(
        self,
        auth: ArkmedsAuth,
        *,
        timeout: float = 5.0,
        max_retries: int = 3,
    ) -> None:
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            token = await self.auth.get_token()
            headers = {"Authorization": f"JWT {token}"}
            self._client = httpx.AsyncClient(
                base_url=self.auth.base_url, 
                timeout=httpx.Timeout(self.timeout), 
                headers=headers,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client

    async def _request(
        self, method: str, url: str, *, params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        client = await self._get_client()

        for attempt in range(self.max_retries):
            try:
                resp = await client.request(method, url, params=params)

                if resp.status_code == 401 and attempt == 0:
                    await self.auth.login()
                    client.headers["Authorization"] = f"JWT {await self.auth.get_token()}"
                    continue

                if resp.status_code == 403:
                    if attempt == 0:
                        await self.auth.login()
                        client.headers["Authorization"] = f"JWT {await self.auth.get_token()}"
                        continue
                    raise ArkmedsAuthError(f"{resp.status_code} {resp.text}")

                if resp.status_code >= 500 or resp.status_code == 429:
                    if attempt == self.max_retries - 1:
                        resp.raise_for_status()
                    await asyncio.sleep(2**attempt)
                    continue

                resp.raise_for_status()
                return resp
            except httpx.RequestError:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)
        raise httpx.HTTPError("Max retries exceeded")

    async def _get_all_pages(self, endpoint: str, params: Dict[str, Any]) -> List[dict]:
        params = params.copy()
        params.setdefault("page", 1)
        params.setdefault("page_size", 100)

        url = endpoint
        results: List[dict] = []
        try:
            while url:
                resp = await self._request("GET", url, params=params if url == endpoint else None)
                data = PaginatedResponse.model_validate(resp.json())
                results.extend(data.results)
                url = data.next
                params = None
        except Exception:
            # Ensure client is closed on error, but ignore cleanup errors
            try:
                await self.close()
            except (RuntimeError, Exception):
                pass
            raise
        return results

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client:
            try:
                await self._client.aclose()
            except (RuntimeError, Exception):
                # Ignore errors during cleanup (like closed event loop)
                pass
            finally:
                self._client = None

    async def list_os(self, **filters: Any) -> List[OS]:
        data = await self._get_all_pages("/api/v3/ordem_servico/", filters)
        return [OS.model_validate(item) for item in data]

    async def list_equipment(self, **filters: Any) -> List[Equipment]:
        data = await self._get_all_pages("/api/v5/company/equipaments/", filters)
        return [Equipment.model_validate(item) for item in data]

    async def list_users(self, **filters: Any) -> List[User]:
        """Lista usuários disponíveis.
        
        Como não há endpoint direto para usuários, extrai de OSs existentes
        e cria cache de usuários únicos baseado nos responsáveis.
        """
        try:
            # Tentar buscar usuários únicos através de OSs
            os_data = await self._get_all_pages("/api/v5/ordem_servico/", {"page_size": 200})
            
            # Extrair usuários únicos dos responsáveis
            usuarios_unicos = {}
            for os in os_data:
                responsavel = os.get("responsavel")
                if responsavel:
                    if isinstance(responsavel, dict):
                        # Responsável é um objeto completo
                        user_id = responsavel.get("id")
                        if user_id and user_id not in usuarios_unicos:
                            usuarios_unicos[user_id] = User.model_validate(responsavel)
                    elif isinstance(responsavel, (int, str)):
                        # Responsável é apenas um ID
                        user_id = int(responsavel)
                        if user_id not in usuarios_unicos:
                            usuarios_unicos[user_id] = User(id=user_id, nome="", email="")
            
            # Retornar lista de usuários únicos
            return list(usuarios_unicos.values())
            
        except (httpx.HTTPStatusError, httpx.RequestError, ConnectionError, RuntimeError) as e:
            # Em caso de erro, retornar usuários padrão mockados
            return [
                User(id=1, nome="Técnico 1", email="tecnico1@example.com"),
                User(id=2, nome="Técnico 2", email="tecnico2@example.com"),
                User(id=3, nome="Supervisor", email="supervisor@example.com"),
            ]

    async def list_tipos(self, **filters: Any) -> List[dict]:
        """Lista tipos de OS disponíveis.
        
        Retorna lista de dicts para manter compatibilidade com UI.
        Use TipoOS enum para validação e type safety.
        """
        try:
            data = await self._get_all_pages("/api/v3/tipo_servico/", filters)
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Endpoint não existe, retornar dados padrão
                return [
                    {"id": 1, "descricao": "Manutenção Preventiva"},
                    {"id": 2, "descricao": "Calibração"},
                    {"id": 3, "descricao": "Manutenção Corretiva"},
                    {"id": 28, "descricao": "Busca Ativa"},
                ]
            raise
        except (httpx.RequestError, ConnectionError, RuntimeError) as e:
            # Em caso de erro de conexão, retornar dados padrão
            return [
                {"id": 1, "descricao": "Manutenção Preventiva"},
                {"id": 2, "descricao": "Calibração"},
                {"id": 3, "descricao": "Manutenção Corretiva"},
                {"id": 28, "descricao": "Busca Ativa"},
            ]

    async def list_estados(self, **filters: Any) -> List[dict]:
        """Lista estados de OS disponíveis.
        
        Retorna lista de dicts para manter compatibilidade com UI.
        Use OSEstado enum para validação e type safety.
        """
        try:
            data = await self._get_all_pages("/api/v3/estado_ordem_servico/", filters)
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Endpoint não existe, retornar dados padrão
                return [
                    {"id": 1, "descricao": "Aberta"},
                    {"id": 2, "descricao": "Fechada"},
                    {"id": 3, "descricao": "Cancelada"},
                ]
            raise
        except (httpx.RequestError, ConnectionError, RuntimeError) as e:
            # Em caso de erro de conexão, retornar dados padrão
            return [
                {"id": 1, "descricao": "Aberta"},
                {"id": 2, "descricao": "Fechada"},
                {"id": 3, "descricao": "Cancelada"},
            ]
    
    async def list_chamados(self, filters: Optional[Dict[str, Any]] = None) -> List[Chamado]:
        """
        Lista chamados da API /api/v5/chamado/.
        
        ⚡ AUDITORIA REALIZADA: 24/07/2025
        📡 Fonte: API /api/v5/chamado/
        📊 Retorna lista de objetos Chamado com dados estruturados
        
        IMPORTANTE: Use page_size e page para controlar a quantidade de dados,
        pois existem mais de 5.000 registros no total.
        """
        if filters is None:
            filters = {}
        
        # Por padrão, incluir chamados arquivados
        filters.setdefault("arquivadas", "true")
        # Limitar a 25 por página se não especificado
        filters.setdefault("page_size", 25)
        filters.setdefault("page", 1)
        
        try:
            # Para chamados, vamos fazer uma única requisição da página especificada
            # ao invés de buscar todas as páginas (que seriam 5.000+ registros)
            params = filters.copy()
            
            client = await self._get_client()
            resp = await client.get("/api/v5/chamado/", params=params)
            resp.raise_for_status()
            
            data = resp.json()
            results = data.get("results", [])
            
            chamados = []
            for item in results:
                try:
                    chamado = Chamado.model_validate(item)
                    chamados.append(chamado)
                except Exception as e:
                    # Log do erro mas continuar processamento
                    print(f"Erro ao processar chamado {item.get('id', 'unknown')}: {e}")
                    continue
            
            return chamados
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise
        except (httpx.RequestError, ConnectionError, RuntimeError):
            return []
    
    async def list_responsaveis_tecnicos(self, filters: Optional[Dict[str, Any]] = None) -> List[ResponsavelTecnico]:
        """
        Lista responsáveis técnicos únicos extraídos dos chamados.
        
        Esta função extrai a lista de responsáveis técnicos únicos
        dos dados de chamados, já que não existe endpoint específico.
        """
        if filters is None:
            filters = {}
        
        try:
            chamados = await self.list_chamados(filters)
            responsaveis_map = {}
            
            for chamado in chamados:
                if chamado.get_resp_tecnico:
                    resp_id = chamado.get_resp_tecnico.id
                    if resp_id not in responsaveis_map:
                        responsaveis_map[resp_id] = chamado.get_resp_tecnico
            
            return list(responsaveis_map.values())
        except Exception:
            return []