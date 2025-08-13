from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import streamlit as st

from .auth import ArkmedsAuth, ArkmedsAuthError
from .models import (
    Chamado,
    Company,
    Equipment,
    PaginatedResponse,
    ResponsavelTecnico,
)


class ArkmedsClient:
    @classmethod
    def from_session(cls) -> ArkmedsClient:
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
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            token = await self.auth.get_token()
            headers = {"Authorization": f"JWT {token}"}
            self._client = httpx.AsyncClient(
                base_url=self.auth.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )
        return self._client

    async def _request(
        self, method: str, url: str, *, params: dict[str, Any] | None = None
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

    async def _get_all_pages(self, endpoint: str, params: dict[str, Any]) -> list[dict]:
        params = params.copy()
        params.setdefault("page", 1)
        params.setdefault("page_size", 100)

        url = endpoint
        results: list[dict] = []
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

    async def list_os(self, **filters: Any) -> list[Chamado]:
        """
        Lista ordens de serviço (agora usando endpoint de chamados com paginação completa).

        CORREÇÃO IMPLEMENTADA: Este método agora usa list_chamados que busca
        TODAS as páginas de resultados, não apenas os primeiros 25 registros.

        Args:
            **filters: Parâmetros de filtro para a API (ex: data_criacao__gte).

        Returns:
            Lista completa de todos os chamados encontrados.
        """
        print(f"📋 list_os chamado com filtros: {filters}")

        # Converter filtros antigos para o novo formato
        filters_dict = dict(filters) if filters else {}

        # Usar o método corrigido com paginação completa
        chamados = await self.list_chamados(filters_dict)

        print(f"✅ list_os retornando {len(chamados)} chamados")

        return chamados

    async def list_equipment(self, **filters: Any) -> list[Equipment]:
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

    async def list_users(self, **filters: Any) -> list[ResponsavelTecnico]:
        """Lista usuários disponíveis.

        MIGRAÇÃO: Agora retorna ResponsavelTecnico extraídos dos chamados.
        """
        return await self.list_responsaveis_tecnicos(dict(filters) if filters else {})

    async def list_tipos(self, **filters: Any) -> list[dict]:
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
        except (httpx.RequestError, ConnectionError, RuntimeError):
            # Em caso de erro de conexão, retornar dados padrão
            return [
                {"id": 1, "descricao": "Manutenção Preventiva"},
                {"id": 2, "descricao": "Calibração"},
                {"id": 3, "descricao": "Manutenção Corretiva"},
                {"id": 28, "descricao": "Busca Ativa"},
            ]

    async def list_estados(self, **filters: Any) -> list[dict]:
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
        except (httpx.RequestError, ConnectionError, RuntimeError):
            # Em caso de erro de conexão, retornar dados padrão
            return [
                {"id": 1, "descricao": "Aberta"},
                {"id": 2, "descricao": "Fechada"},
                {"id": 3, "descricao": "Cancelada"},
            ]

    async def list_chamados(self, filters: dict[str, Any] | None = None) -> list[Chamado]:
        """
        Lista chamados da API /api/v5/chamado/ com paginação completa.

        ⚡ CORREÇÃO IMPLEMENTADA: Agora busca TODAS as páginas de resultados
        📡 Fonte: API /api/v5/chamado/
        📊 Retorna lista completa de objetos Chamado com dados estruturados

        IMPORTANTE: Esta função agora implementa paginação completa para resolver
        o problema dos KPIs mostrando apenas 25 registros.
        """
        if filters is None:
            filters = {}

        # Extrair filtros locais que não são suportados pela API
        local_filter_estados = filters.pop("_local_filter_estados", None)

        # Configurações para paginação completa
        filters.setdefault("arquivadas", "true")
        filters.setdefault("page_size", 100)  # Máximo permitido pela API

        all_results = []
        page = 1
        total_pages = 0
        total_time = 0

        # Log inicial
        print("🔍 Iniciando busca de chamados com paginação completa...")
        print(f"📋 Filtros aplicados: {filters}")
        print("-" * 60)

        try:
            client = await self._get_client()

            while True:
                params = filters.copy()
                params["page"] = page

                start_time = time.time()

                print(f"\n🔍 Buscando página {page}...")
                resp = await client.get("/api/v5/chamado/", params=params)
                resp.raise_for_status()

                elapsed = time.time() - start_time
                total_time += elapsed

                data = resp.json()
                results = data.get("results", [])
                total_count = data.get("count", 0)
                has_next = data.get("next") is not None

                print(f"✅ Página {page} recebida em {elapsed:.2f}s")
                print(f"   - Registros nesta página: {len(results)}")
                print(f"   - Total de registros na API: {total_count}")
                print(f"   - Tem próxima página: {has_next}")

                if not results:
                    print("❌ Página vazia, finalizando busca")
                    break

                all_results.extend(results)
                total_pages = page

                # Mostrar progresso
                progress = (len(all_results) / total_count * 100) if total_count > 0 else 0
                print(f"📊 Progresso: {len(all_results)}/{total_count} ({progress:.1f}%)")

                # Verificar se há próxima página
                if has_next:
                    page += 1
                else:
                    print("✅ Não há mais páginas, finalizando busca")
                    break

            # Resumo da busca
            print("\n" + "=" * 60)
            print("BUSCA FINALIZADA - RESUMO:")
            print(f"✅ Total de páginas processadas: {total_pages}")
            print(f"✅ Total de registros brutos obtidos: {len(all_results)}")
            print(f"✅ Tempo total: {total_time:.2f}s")
            print(
                f"✅ Tempo médio por página: {total_time/total_pages:.2f}s"
                if total_pages > 0
                else "N/A"
            )
            print("=" * 60)

            # Converter para objetos Chamado
            print(f"\n🔄 Convertendo {len(all_results)} registros para objetos Chamado...")
            chamados = []
            conversion_errors = 0
            sem_os_count = 0
            sem_responsavel_count = 0

            for item in all_results:
                try:
                    # Verificar se tem ordem_servico antes de tentar converter
                    if "ordem_servico" not in item or item["ordem_servico"] is None:
                        sem_os_count += 1
                        # Para incluir chamados sem OS, descomente a linha abaixo
                        # chamados.append(Chamado.model_validate(item))
                        continue

                    # Verificar se tem responsável técnico
                    if (
                        item.get("responsavel_id") is None
                        and item.get("get_resp_tecnico", {}).get("has_resp_tecnico") is False
                    ):
                        sem_responsavel_count += 1

                    chamado = Chamado.model_validate(item)

                    # Aplicar filtro local de estados se especificado
                    if local_filter_estados and chamado.ordem_servico:
                        # Verificar se a OS tem um estado nos filtros especificados
                        estado_id = None
                        if hasattr(chamado.ordem_servico.get("estado"), "id"):
                            estado_id = chamado.ordem_servico.get("estado").id
                        elif isinstance(chamado.ordem_servico.get("estado"), int):
                            estado_id = chamado.ordem_servico.get("estado")

                        if estado_id is not None and estado_id not in local_filter_estados:
                            continue

                    chamados.append(chamado)
                except Exception as e:
                    conversion_errors += 1
                    if conversion_errors <= 5:  # Mostrar apenas os primeiros 5 erros
                        print(f"⚠️ Erro ao processar chamado {item.get('id', 'unknown')}: {e}")
                    continue

            if conversion_errors > 5:
                print(f"⚠️ ... e mais {conversion_errors - 5} erros de conversão")

            # Aplicar filtros locais se necessário
            original_count = len(chamados)
            if local_filter_estados:
                print(f"\n🔍 Aplicando filtro local de estados: {local_filter_estados}")
                print(f"📊 Filtro de estados: {original_count} chamados processados")

            print(f"\n✅ RESULTADO FINAL: {len(chamados)} chamados válidos retornados")
            print(f"   - Registros brutos da API: {len(all_results)}")
            print(f"   - Chamados sem ordem de serviço: {sem_os_count}")
            print(f"   - Chamados sem responsável técnico: {sem_responsavel_count}")
            print(f"   - Erros de conversão: {conversion_errors}")
            print(f"   - Chamados válidos finais: {len(chamados)}")

            return chamados

        except httpx.HTTPStatusError as e:
            print(f"❌ Erro HTTP: {e.response.status_code} - {e.response.text[:200]}")
            if e.response.status_code == 404:
                return []
            raise
        except (httpx.RequestError, ConnectionError, RuntimeError) as e:
            print(f"❌ Erro de conexão: {e!s}")
            return []

    async def list_responsaveis_tecnicos(
        self, filters: dict[str, Any] | None = None
    ) -> list[ResponsavelTecnico]:
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

    async def list_companies_equipamentos(self) -> list[Company]:
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

    async def list_equipamentos(self, filters: dict[str, Any] | None = None) -> list[Equipment]:
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

    async def get_equipamento(self, equipamento_id: int) -> Equipment | None:
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
