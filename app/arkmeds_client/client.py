from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
import streamlit as st

from .auth import ArkmedsAuth, ArkmedsAuthError
from .models import (
    Equipment,
    OSEstado,
    PaginatedResponse,
    TipoOS,
    Chamado,
    ResponsavelTecnico,
    Company,
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
        timeout: float = 15.0,
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
                resp = await self._request("GET", url, params=params if url == endpoint else {})
                data = PaginatedResponse.model_validate(resp.json())
                results.extend(data.results)
                url = data.next
                params = {}
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

    async def list_os(self, **filters: Any) -> List[Chamado]:
        """
        Lista ordens de serviço (agora usando endpoint de chamados).
        
        MIGRAÇÃO: Este método agora retorna dados de Chamado que 
        contêm informações mais ricas incluindo dados da OS associada.
        """
        # Converter filtros antigos para o novo formato
        filters_dict = dict(filters) if filters else {}
        return await self.list_chamados(filters_dict)

    async def list_equipment(self, **filters: Any) -> List[Equipment]:
        """Lista todos os equipamentos extraindo-os das empresas.
        
        O endpoint /api/v5/company/equipaments/ retorna empresas com equipamentos aninhados.
        Esta função extrai todos os equipamentos de todas as empresas.
        """
        companies_data = await self._get_all_pages("/api/v5/company/equipaments/", filters)
        
        # Extrair todos os equipamentos de todas as empresas
        all_equipment = []
        for company in companies_data:
            equipamentos = company.get("equipamentos", [])
            for equip_data in equipamentos:
                # Adicionar o ID da empresa proprietária se disponível
                if "proprietario" not in equip_data and "id" in company:
                    equip_data["proprietario"] = company["id"]
                all_equipment.append(equip_data)
        
        return [Equipment.model_validate(item) for item in all_equipment]

    async def list_users(self, **filters: Any) -> List[ResponsavelTecnico]:
        """Lista usuários disponíveis.
        
        MIGRAÇÃO: Agora retorna ResponsavelTecnico extraídos dos chamados.
        """
        return await self.list_responsaveis_tecnicos(dict(filters) if filters else {})

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

    async def list_companies_equipamentos(self) -> List[Company]:
        """Lista todas as empresas com seus equipamentos.
        
        Returns:
            Lista de empresas com equipamentos aninhados
            
        Raises:
            ArkmedsClientError: Se houver erro na requisição
        """
        try:
            response = await self._request("GET", "/api/v5/company/equipaments/")
            data = response.json()
            
            if not data.get("results"):
                return []
            
            companies = []
            for company_data in data["results"]:
                company = Company(**company_data)
                companies.append(company)
            
            return companies
        except Exception as e:
            print(f"Erro ao listar empresas: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def list_equipamentos(self, filters: Optional[Dict[str, Any]] = None) -> List[Equipment]:
        """Lista todos os equipamentos de todas as empresas.
        
        Args:
            filters: Filtros opcionais para aplicar
            
        Returns:
            Lista de equipamentos de todas as empresas
            
        Raises:
            ArkmedsClientError: Se houver erro na requisição
        """
        try:
            companies = await self.list_companies_equipamentos()
            equipamentos = []
            
            for company in companies:
                for equip_data in company.equipamentos:
                    # Adiciona o proprietario (empresa) aos dados do equipamento
                    equip_data["proprietario"] = company.id
                    equipamento = Equipment(**equip_data)
                    equipamentos.append(equipamento)
            
            return equipamentos
        except Exception as e:
            print(f"Erro ao listar equipamentos: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def get_equipamento(self, equipamento_id: int) -> Optional[Equipment]:
        """Busca um equipamento específico pelo ID.
        
        Args:
            equipamento_id: ID do equipamento
            
        Returns:
            Equipamento encontrado ou None se não existir
            
        Raises:
            ArkmedsClientError: Se houver erro na requisição
        """
        try:
            response = await self._request("GET", f"/api/v5/equipament/{equipamento_id}/")
            data = response.json()
            if data:
                return Equipment(**data)
            return None
        except Exception as e:
            print(f"Erro ao buscar equipamento {equipamento_id}: {e}")
            import traceback
            traceback.print_exc()
            return None